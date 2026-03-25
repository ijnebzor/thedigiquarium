//! Candle on Metal inference backend.
//!
//! Loads GGUF quantized models via candle-transformers and runs inference
//! on Apple GPU using Metal shaders. Targets Qwen3-0.6B as the primary model.
//!
//! Uses `quantized_llama::ModelWeights` which is compatible with Qwen3 GGUF files
//! (shared architecture format). When candle-transformers publishes a release with
//! `quantized_qwen3`, this module should switch to it for native Qwen3 support
//! including `clear_kv_cache()` — until then, we reload the model per conversation
//! to ensure a clean KV cache.

use std::path::PathBuf;
use std::pin::Pin;
use std::sync::{Arc, Mutex};

use anyhow::{Context, Result};
use candle_core::quantized::gguf_file;
use candle_core::{Device, IndexOp, Tensor};
use candle_transformers::generation::LogitsProcessor;
use candle_transformers::models::quantized_llama::ModelWeights;
use tokenizers::Tokenizer;
use tracing::{debug, info, warn};

use aquarium_core::{
    Completion, FinishReason, GenerationConfig, InferenceProvider, Message, Role, Tool, Usage,
};
use crate::parse_tool_calls;

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/// Configuration for the Candle on Metal backend.
#[derive(Debug, Clone)]
pub struct CandleConfig {
    /// HuggingFace repo ID for the GGUF model (e.g., `Qwen/Qwen3-0.6B-GGUF`).
    pub model_repo: String,
    /// GGUF filename within the repo (e.g., `qwen3-0.6b-q4_k_m.gguf`).
    pub model_file: String,
    /// HuggingFace repo ID for the tokenizer (e.g., `Qwen/Qwen3-0.6B`).
    pub tokenizer_repo: String,
}

impl CandleConfig {
    /// Default config for Qwen3-0.6B with Q4_K_M quantization.
    pub fn qwen3_0_6b() -> Self {
        Self {
            model_repo: "Qwen/Qwen3-0.6B-GGUF".into(),
            model_file: "qwen3-0.6b-q4_k_m.gguf".into(),
            tokenizer_repo: "Qwen/Qwen3-0.6B".into(),
        }
    }

    /// Construct from a model ID and optional quantization suffix.
    ///
    /// Maps e.g. `"Qwen/Qwen3-0.6B"` + `"q4_k_m"` to the correct GGUF repo,
    /// filename, and tokenizer repo.
    pub fn from_model_id(model_id: &str, quantization: Option<&str>) -> Self {
        let quant = quantization.unwrap_or("q4_k_m");
        let model_name = model_id.split('/').last().unwrap_or(model_id);
        Self {
            model_repo: format!("{model_id}-GGUF"),
            model_file: format!("{}-{quant}.gguf", model_name.to_lowercase()),
            tokenizer_repo: model_id.to_string(),
        }
    }
}

// ---------------------------------------------------------------------------
// Backend
// ---------------------------------------------------------------------------

/// In-process inference on Apple Metal GPU via candle.
///
/// Loads a GGUF quantized model and runs autoregressive text generation.
/// Tool calling is handled by parsing the model's text output (not native) —
/// callers should inject tool descriptions into the system prompt using
/// `aquarium_core::prompt::tools_as_prompt_text()`.
///
/// **KV cache management**: Since `quantized_llama::ModelWeights` in candle 0.8
/// does not expose `clear_kv_cache()`, we reload the model from the cached GGUF
/// file at the start of each generation to guarantee a clean KV state. The OS
/// page cache makes subsequent loads fast (~100ms for 350MB).
pub struct CandleBackend {
    /// Path to the downloaded GGUF file on disk (cached by hf-hub).
    model_path: PathBuf,
    tokenizer: Arc<Tokenizer>,
    device: Device,
    #[allow(dead_code)] // Retained for debugging and future config access.
    config: CandleConfig,
    /// Token IDs that signal end of generation.
    eos_tokens: Vec<u32>,
    /// Mutex-guarded model for concurrent safety. Reloaded per conversation.
    model: Arc<Mutex<Option<ModelWeights>>>,
}

impl CandleBackend {
    /// Load a GGUF model from HuggingFace Hub.
    ///
    /// Downloads model and tokenizer files on first use (cached by hf-hub).
    /// Attempts to use Metal (Apple GPU); falls back to CPU if unavailable.
    pub fn load(config: CandleConfig) -> Result<Self> {
        info!(
            repo = %config.model_repo,
            file = %config.model_file,
            "Loading GGUF model"
        );

        let device = select_device();

        // Download files via HuggingFace Hub (cached after first download).
        let api =
            hf_hub::api::sync::Api::new().context("Failed to initialize HuggingFace Hub API")?;

        let model_path = api
            .model(config.model_repo.clone())
            .get(&config.model_file)
            .context("Failed to download GGUF model file")?;

        let tokenizer_path = api
            .model(config.tokenizer_repo.clone())
            .get("tokenizer.json")
            .context("Failed to download tokenizer")?;

        // Do an initial load to verify the model file is valid.
        let model = load_model_weights(&model_path, &device)?;

        let tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| anyhow::anyhow!("Failed to load tokenizer: {e}"))?;

        let eos_tokens: Vec<u32> = ["<|im_end|>", "<|endoftext|>", "<|end|>"]
            .iter()
            .filter_map(|s| tokenizer.token_to_id(s))
            .collect();

        debug!(?eos_tokens, "Resolved EOS tokens");
        info!("Model loaded and verified successfully");

        Ok(Self {
            model_path,
            tokenizer: Arc::new(tokenizer),
            device,
            config,
            eos_tokens,
            model: Arc::new(Mutex::new(Some(model))),
        })
    }

    /// Load from a local GGUF file path (no HuggingFace download).
    pub fn load_from_path(
        model_path: impl Into<PathBuf>,
        tokenizer_path: impl AsRef<std::path::Path>,
        config: CandleConfig,
    ) -> Result<Self> {
        let model_path = model_path.into();
        let device = select_device();

        let model = load_model_weights(&model_path, &device)?;

        let tokenizer = Tokenizer::from_file(tokenizer_path.as_ref())
            .map_err(|e| anyhow::anyhow!("Failed to load tokenizer: {e}"))?;

        let eos_tokens: Vec<u32> = ["<|im_end|>", "<|endoftext|>", "<|end|>"]
            .iter()
            .filter_map(|s| tokenizer.token_to_id(s))
            .collect();

        Ok(Self {
            model_path,
            tokenizer: Arc::new(tokenizer),
            device,
            config,
            eos_tokens,
            model: Arc::new(Mutex::new(Some(model))),
        })
    }
}

impl InferenceProvider for CandleBackend {
    fn complete(
        &self,
        messages: &[Message],
        _tools: &[Tool],
        config: &GenerationConfig,
    ) -> Pin<Box<dyn std::future::Future<Output = Result<Completion>> + Send + '_>> {
        let messages = messages.to_vec();
        let config = config.clone();
        let model_arc = Arc::clone(&self.model);
        let tokenizer = Arc::clone(&self.tokenizer);
        let device = self.device.clone();
        let eos_tokens = self.eos_tokens.clone();
        let model_path = self.model_path.clone();

        Box::pin(async move {
            if messages.is_empty() {
                anyhow::bail!("Messages cannot be empty");
            }

            let prompt = format_chatml(&messages);

            tokio::task::spawn_blocking(move || {
                generate(
                    &model_arc,
                    &model_path,
                    &tokenizer,
                    &device,
                    &config,
                    &eos_tokens,
                    &prompt,
                )
            })
            .await
            .context("Generation task panicked")?
        })
    }

    fn name(&self) -> &str {
        "candle-metal"
    }

    fn supports_native_tools(&self) -> bool {
        false
    }
}

// ---------------------------------------------------------------------------
// Model loading
// ---------------------------------------------------------------------------

fn select_device() -> Device {
    match Device::new_metal(0) {
        Ok(d) => {
            info!("Using Metal GPU for inference");
            d
        }
        Err(e) => {
            warn!("Metal unavailable ({e}), falling back to CPU");
            Device::Cpu
        }
    }
}

fn load_model_weights(path: &std::path::Path, device: &Device) -> Result<ModelWeights> {
    let mut file = std::fs::File::open(path).context("Failed to open GGUF model file")?;
    let content = gguf_file::Content::read(&mut file)
        .map_err(|e| anyhow::anyhow!("Failed to read GGUF content: {e}"))?;
    let model = ModelWeights::from_gguf(content, &mut file, device)
        .map_err(|e| anyhow::anyhow!("Failed to load model weights: {e}"))?;
    Ok(model)
}

// ---------------------------------------------------------------------------
// ChatML formatting
// ---------------------------------------------------------------------------

/// Format messages using the ChatML template (used by Qwen3, Qwen2.5, etc.).
///
/// ```text
/// <|im_start|>system
/// You are a helpful assistant.<|im_end|>
/// <|im_start|>user
/// Hello<|im_end|>
/// <|im_start|>assistant
/// ```
///
/// Only appends the assistant turn opener if the last message is not already
/// from the assistant (avoids duplicate turn headers on continuation).
fn format_chatml(messages: &[Message]) -> String {
    let mut prompt = String::new();
    for msg in messages {
        let role = match msg.role {
            Role::System => "system",
            Role::User => "user",
            Role::Assistant => "assistant",
            Role::Tool => "tool",
        };
        prompt.push_str("<|im_start|>");
        prompt.push_str(role);
        prompt.push('\n');
        prompt.push_str(&msg.content);
        prompt.push_str("<|im_end|>\n");
    }
    // Only open the assistant turn if the last message isn't already from assistant.
    if messages.last().map(|m| m.role) != Some(Role::Assistant) {
        prompt.push_str("<|im_start|>assistant\n");
    }
    prompt
}

// ---------------------------------------------------------------------------
// Text generation
// ---------------------------------------------------------------------------

/// Run autoregressive text generation (synchronous — called via spawn_blocking).
///
/// Reloads the model from disk to guarantee clean KV cache state. The GGUF file
/// is kept in the OS page cache, making reloads fast after the initial download.
fn generate(
    model_arc: &Mutex<Option<ModelWeights>>,
    model_path: &std::path::Path,
    tokenizer: &Tokenizer,
    device: &Device,
    config: &GenerationConfig,
    eos_tokens: &[u32],
    prompt: &str,
) -> Result<Completion> {
    // Take the existing model or reload from disk.
    // We take ownership (Option::take) so the next call will reload fresh,
    // guaranteeing a clean KV cache.
    let mut model = {
        let mut guard = model_arc
            .lock()
            .map_err(|e| anyhow::anyhow!("Model lock poisoned: {e}"))?;
        match guard.take() {
            Some(m) => m,
            None => {
                debug!("Reloading model from disk for clean KV cache");
                load_model_weights(model_path, device)?
            }
        }
    };

    // Tokenize the prompt.
    let encoding = tokenizer
        .encode(prompt, true)
        .map_err(|e| anyhow::anyhow!("Tokenization failed: {e}"))?;
    let prompt_tokens = encoding.get_ids();
    let prompt_len = prompt_tokens.len();

    if prompt_tokens.is_empty() {
        anyhow::bail!("Empty prompt after tokenization");
    }

    debug!(prompt_len, max_tokens = config.max_tokens, "Starting generation");

    // Set up sampling.
    let seed = config.seed.unwrap_or_else(|| {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64
    });

    let mut logits_processor =
        LogitsProcessor::new(seed, Some(config.temperature), config.top_p);

    let mut generated_tokens: Vec<u32> = Vec::new();
    let mut finish_reason = FinishReason::MaxTokens;

    // --- Prefill: process all prompt tokens at once ---
    let input = Tensor::new(prompt_tokens, device)?.unsqueeze(0)?;
    let logits = model.forward(&input, 0)?;
    let logits = extract_last_logits(&logits)?;
    let mut next_token = logits_processor.sample(&logits)?;

    if eos_tokens.contains(&next_token) {
        finish_reason = FinishReason::Stop;
        return Ok(Completion {
            content: String::new(),
            tool_calls: vec![],
            usage: Some(Usage {
                prompt_tokens: Some(prompt_len as u32),
                completion_tokens: Some(0),
            }),
            finish_reason,
        });
    }
    generated_tokens.push(next_token);

    // --- Decode: generate one token at a time ---
    let max_tokens = config.max_tokens.min(4096) as usize; // Safety cap
    for i in 1..max_tokens {
        let start_pos = prompt_len + i - 1;
        let input = Tensor::new(&[next_token], device)?.unsqueeze(0)?;
        let logits = model.forward(&input, start_pos)?;
        let logits = extract_last_logits(&logits)?;
        next_token = logits_processor.sample(&logits)?;

        if eos_tokens.contains(&next_token) {
            finish_reason = FinishReason::Stop;
            break;
        }
        generated_tokens.push(next_token);
    }

    // Decode generated tokens back to text.
    let output = tokenizer
        .decode(&generated_tokens, true)
        .map_err(|e| anyhow::anyhow!("Token decoding failed: {e}"))?;

    debug!(
        generated_len = generated_tokens.len(),
        output_len = output.len(),
        "Generation complete"
    );

    // Parse tool calls from the generated text.
    let tool_calls = parse_tool_calls(&output);
    if !tool_calls.is_empty() {
        finish_reason = FinishReason::ToolCall;
    }

    Ok(Completion {
        content: output,
        tool_calls,
        usage: Some(Usage {
            prompt_tokens: Some(prompt_len as u32),
            completion_tokens: Some(generated_tokens.len() as u32),
        }),
        finish_reason,
    })
}

/// Extract logits for the last sequence position, handling varying tensor ranks.
fn extract_last_logits(logits: &Tensor) -> Result<Tensor> {
    let dims = logits.dims();
    match dims.len() {
        1 => Ok(logits.clone()),
        2 => Ok(logits.i(dims[0] - 1)?),
        3 => Ok(logits.i((0, dims[1] - 1))?),
        n => anyhow::bail!("Unexpected logits tensor rank {n}, shape: {dims:?}"),
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chatml_formatting() {
        let messages = vec![
            Message::system("You are a helpful assistant."),
            Message::user("Hello"),
        ];
        let prompt = format_chatml(&messages);
        assert!(prompt.contains("<|im_start|>system\nYou are a helpful assistant.<|im_end|>"));
        assert!(prompt.contains("<|im_start|>user\nHello<|im_end|>"));
        assert!(prompt.ends_with("<|im_start|>assistant\n"));
    }

    #[test]
    fn chatml_multi_turn() {
        let messages = vec![
            Message::system("System prompt."),
            Message::user("First question"),
            Message::assistant("First answer"),
            Message::user("Follow-up"),
        ];
        let prompt = format_chatml(&messages);
        let starts = prompt.matches("<|im_start|>").count();
        assert_eq!(starts, 5); // 4 messages + 1 assistant generation prompt
    }

    #[test]
    fn chatml_no_duplicate_assistant_opener() {
        let messages = vec![
            Message::system("System prompt."),
            Message::user("Hello"),
            Message::assistant("Partial response"),
        ];
        let prompt = format_chatml(&messages);
        // Last message is assistant — should NOT add another assistant opener.
        assert!(prompt.ends_with("Partial response<|im_end|>\n"));
        let assistant_starts = prompt.matches("<|im_start|>assistant").count();
        assert_eq!(assistant_starts, 1); // Only the one from the message itself
    }

    #[test]
    fn chatml_empty_messages() {
        let messages: Vec<Message> = vec![];
        let prompt = format_chatml(&messages);
        // No messages, but still opens assistant turn.
        assert_eq!(prompt, "<|im_start|>assistant\n");
    }

    #[test]
    fn candle_config_from_model_id() {
        let config = CandleConfig::from_model_id("Qwen/Qwen3-0.6B", Some("q4_k_m"));
        assert_eq!(config.model_repo, "Qwen/Qwen3-0.6B-GGUF");
        assert_eq!(config.model_file, "qwen3-0.6b-q4_k_m.gguf");
        assert_eq!(config.tokenizer_repo, "Qwen/Qwen3-0.6B");
    }

    #[test]
    fn candle_config_from_model_id_default_quant() {
        let config = CandleConfig::from_model_id("Qwen/Qwen3-0.6B", None);
        assert_eq!(config.model_file, "qwen3-0.6b-q4_k_m.gguf");
    }
}
