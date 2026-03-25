//! Ollama / LM Studio HTTP backend.
//!
//! Connects to a running Ollama or LM Studio server via the `/api/chat` endpoint.
//! Supports native tool calling for models that handle it (Qwen3, LFM2.5, etc.).
//!
//! Default endpoint: `http://localhost:11434`
//!
//! Target models:
//! - **Qwen3-0.6B** (`qwen3:0.6b`) — 0.880 tool score, ~350MB, perfect restraint
//! - **LFM2.5-1.2B** (`lfm2:1.2b`) — 0.880 tool score, ~731MB, fastest inference

use std::pin::Pin;
use std::time::Duration;

use anyhow::{Context, Result};
use serde::Deserialize;
use tracing::{debug, warn};

use aquarium_core::{
    Completion, FinishReason, GenerationConfig, InferenceProvider, Message, Role, Tool, ToolCall,
    Usage,
};

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/// Configuration for the Ollama backend.
#[derive(Debug, Clone)]
pub struct OllamaConfig {
    /// Base URL of the Ollama server (without trailing slash).
    pub base_url: String,
    /// Model name as known to Ollama (e.g., `qwen3:0.6b`).
    pub model: String,
    /// Timeout for the full request (including model generation).
    pub request_timeout: Duration,
    /// Timeout for initial TCP connection.
    pub connect_timeout: Duration,
    /// Maximum retry attempts for transient failures.
    pub max_retries: u32,
    /// Base delay between retries (multiplied by attempt number).
    pub retry_backoff: Duration,
}

impl Default for OllamaConfig {
    fn default() -> Self {
        Self {
            base_url: "http://localhost:11434".into(),
            model: "qwen3:0.6b".into(),
            request_timeout: Duration::from_secs(120),
            connect_timeout: Duration::from_secs(10),
            max_retries: 3,
            retry_backoff: Duration::from_secs(1),
        }
    }
}

// ---------------------------------------------------------------------------
// Backend
// ---------------------------------------------------------------------------

/// HTTP client for Ollama / LM Studio local inference servers.
///
/// Sends chat completion requests to the Ollama `/api/chat` endpoint with
/// optional native tool calling support. Non-streaming mode with retry logic.
#[derive(Clone)]
pub struct OllamaBackend {
    client: reqwest::Client,
    config: OllamaConfig,
}

impl OllamaBackend {
    /// Create a new Ollama backend with the given configuration.
    ///
    /// Configures the HTTP client with connect and request timeouts.
    pub fn new(config: OllamaConfig) -> Result<Self> {
        let client = reqwest::Client::builder()
            .connect_timeout(config.connect_timeout)
            .timeout(config.request_timeout)
            .build()
            .context("Failed to build HTTP client")?;
        Ok(Self { client, config })
    }

    /// Create with default config (localhost:11434, Qwen3-0.6B).
    pub fn default_qwen3() -> Result<Self> {
        Self::new(OllamaConfig::default())
    }

    /// Check that Ollama is reachable and the configured model is available.
    pub async fn health_check(&self) -> Result<()> {
        let url = format!("{}/api/tags", self.config.base_url);
        let resp = self
            .client
            .get(&url)
            .send()
            .await
            .context("Cannot reach Ollama — is it running?")?;

        if !resp.status().is_success() {
            anyhow::bail!("Ollama health check returned {}", resp.status());
        }

        let body: OllamaTagsResponse = resp
            .json()
            .await
            .context("Invalid response from Ollama /api/tags")?;

        let model_exists = body.models.iter().any(|m| {
            m.name == self.config.model || m.name.starts_with(&format!("{}:", self.config.model))
        });

        if !model_exists {
            let available: Vec<&str> = body.models.iter().map(|m| m.name.as_str()).collect();
            anyhow::bail!(
                "Model '{}' not found in Ollama. Available: {:?}. Run `ollama pull {}` first.",
                self.config.model,
                available,
                self.config.model,
            );
        }

        debug!(model = %self.config.model, "Ollama health check passed");
        Ok(())
    }
}

impl InferenceProvider for OllamaBackend {
    fn complete(
        &self,
        messages: &[Message],
        tools: &[Tool],
        config: &GenerationConfig,
    ) -> Pin<Box<dyn std::future::Future<Output = Result<Completion>> + Send + '_>> {
        let messages = messages.to_vec();
        let tools = tools.to_vec();
        let config = config.clone();

        Box::pin(async move {
            if messages.is_empty() {
                anyhow::bail!("Messages cannot be empty");
            }

            let url = format!("{}/api/chat", self.config.base_url);

            let body = build_request_body(&self.config, &messages, &tools, &config);

            let mut last_err = None;

            for attempt in 0..=self.config.max_retries {
                if attempt > 0 {
                    let backoff = self.config.retry_backoff * attempt;
                    warn!(attempt, backoff_ms = backoff.as_millis(), "Retrying Ollama request");
                    tokio::time::sleep(backoff).await;
                }

                match self.send_request(&url, &body).await {
                    Ok(completion) => return Ok(completion),
                    Err(e) => {
                        if is_transient(&e) {
                            warn!(attempt, error = %e, "Transient Ollama error");
                            last_err = Some(e);
                            continue;
                        }
                        return Err(e);
                    }
                }
            }

            Err(last_err
                .unwrap_or_else(|| anyhow::anyhow!("Ollama request failed after all retries")))
        })
    }

    fn name(&self) -> &str {
        "ollama"
    }

    fn supports_native_tools(&self) -> bool {
        true
    }
}

impl OllamaBackend {
    async fn send_request(
        &self,
        url: &str,
        body: &serde_json::Value,
    ) -> Result<Completion> {
        debug!("POST {url} model={}", self.config.model);

        let response = self
            .client
            .post(url)
            .json(body)
            .send()
            .await
            .context("Failed to connect to Ollama — is it running on localhost:11434?")?;

        let status = response.status();
        if !status.is_success() {
            let text = response.text().await.unwrap_or_default();
            match status.as_u16() {
                404 => anyhow::bail!(
                    "Model '{}' not found. Run `ollama pull {}` first. Response: {text}",
                    self.config.model,
                    self.config.model,
                ),
                429 => anyhow::bail!("Ollama rate limited: {text}"),
                s if (500..600).contains(&s) => {
                    anyhow::bail!("Ollama server error ({status}): {text}")
                }
                _ => anyhow::bail!("Ollama returned {status}: {text}"),
            }
        }

        let resp: OllamaChatResponse = response
            .json()
            .await
            .context("Failed to parse Ollama response JSON")?;

        let tool_calls: Vec<ToolCall> = resp
            .message
            .tool_calls
            .into_iter()
            .enumerate()
            .map(|(i, tc)| ToolCall {
                id: Some(format!("ollama_call_{i}")),
                tool: tc.function.name,
                arguments: tc.function.arguments,
            })
            .collect();

        let finish_reason = if !tool_calls.is_empty() {
            FinishReason::ToolCall
        } else {
            FinishReason::Stop
        };

        let usage = Some(Usage {
            prompt_tokens: resp.prompt_eval_count,
            completion_tokens: resp.eval_count,
        });

        debug!(
            content_len = resp.message.content.len(),
            tool_calls = tool_calls.len(),
            "Ollama completion received"
        );

        Ok(Completion {
            content: resp.message.content,
            tool_calls,
            usage,
            finish_reason,
        })
    }
}

// ---------------------------------------------------------------------------
// Request building
// ---------------------------------------------------------------------------

fn build_request_body(
    ollama_config: &OllamaConfig,
    messages: &[Message],
    tools: &[Tool],
    config: &GenerationConfig,
) -> serde_json::Value {
    let ollama_messages: Vec<serde_json::Value> = messages
        .iter()
        .map(|m| {
            serde_json::json!({
                "role": role_str(&m.role),
                "content": &m.content,
            })
        })
        .collect();

    let ollama_tools: Vec<serde_json::Value> = tools
        .iter()
        .map(|t| {
            serde_json::json!({
                "type": "function",
                "function": {
                    "name": &t.name,
                    "description": &t.description,
                    "parameters": &t.parameters,
                }
            })
        })
        .collect();

    let mut options = serde_json::json!({
        "temperature": config.temperature,
        "num_predict": config.max_tokens,
    });
    if let Some(top_p) = config.top_p {
        options["top_p"] = serde_json::json!(top_p);
    }
    if let Some(top_k) = config.top_k {
        options["top_k"] = serde_json::json!(top_k);
    }
    if let Some(repeat_penalty) = config.repeat_penalty {
        options["repeat_penalty"] = serde_json::json!(repeat_penalty);
    }
    if let Some(seed) = config.seed {
        options["seed"] = serde_json::json!(seed);
    }

    let mut body = serde_json::json!({
        "model": &ollama_config.model,
        "messages": ollama_messages,
        "stream": false,
        "options": options,
    });

    if !ollama_tools.is_empty() {
        body["tools"] = serde_json::Value::Array(ollama_tools);
    }

    body
}

fn role_str(role: &Role) -> &'static str {
    match role {
        Role::System => "system",
        Role::User => "user",
        Role::Assistant => "assistant",
        Role::Tool => "tool",
    }
}

/// Check whether an error is transient (worth retrying).
fn is_transient(e: &anyhow::Error) -> bool {
    if let Some(reqwest_err) = e.downcast_ref::<reqwest::Error>() {
        return reqwest_err.is_connect() || reqwest_err.is_timeout();
    }
    let msg = e.to_string();
    msg.contains("rate limited") || msg.contains("server error")
}

// ---------------------------------------------------------------------------
// Ollama API response types
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
struct OllamaChatResponse {
    message: OllamaResponseMessage,
    #[serde(default)]
    prompt_eval_count: Option<u32>,
    #[serde(default)]
    eval_count: Option<u32>,
}

#[derive(Debug, Deserialize)]
struct OllamaResponseMessage {
    #[serde(default)]
    content: String,
    #[serde(default)]
    tool_calls: Vec<OllamaToolCall>,
}

#[derive(Debug, Deserialize)]
struct OllamaToolCall {
    function: OllamaFunction,
}

#[derive(Debug, Deserialize)]
struct OllamaFunction {
    name: String,
    arguments: serde_json::Value,
}

#[derive(Debug, Deserialize)]
struct OllamaTagsResponse {
    models: Vec<OllamaModelInfo>,
}

#[derive(Debug, Deserialize)]
struct OllamaModelInfo {
    name: String,
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_config() {
        let config = OllamaConfig::default();
        assert_eq!(config.base_url, "http://localhost:11434");
        assert_eq!(config.model, "qwen3:0.6b");
        assert_eq!(config.request_timeout, Duration::from_secs(120));
        assert_eq!(config.max_retries, 3);
    }

    #[test]
    fn build_request_body_basic() {
        let ollama_config = OllamaConfig::default();
        let messages = vec![Message::system("sys"), Message::user("hello")];
        let gen_config = GenerationConfig::default();
        let body = build_request_body(&ollama_config, &messages, &[], &gen_config);

        assert_eq!(body["model"], "qwen3:0.6b");
        assert_eq!(body["stream"], false);
        assert_eq!(body["messages"].as_array().unwrap().len(), 2);
        assert_eq!(body["messages"][0]["role"], "system");
        assert_eq!(body["messages"][1]["role"], "user");
        assert!(body.get("tools").is_none());
    }

    #[test]
    fn build_request_body_with_tools() {
        let ollama_config = OllamaConfig::default();
        let messages = vec![Message::user("search for music")];
        let tools = vec![Tool {
            name: "search".into(),
            description: "Search articles".into(),
            parameters: serde_json::json!({"type": "object"}),
        }];
        let gen_config = GenerationConfig::default();
        let body = build_request_body(&ollama_config, &messages, &tools, &gen_config);

        let tools_arr = body["tools"].as_array().unwrap();
        assert_eq!(tools_arr.len(), 1);
        assert_eq!(tools_arr[0]["function"]["name"], "search");
    }

    #[test]
    fn build_request_body_with_generation_config() {
        let ollama_config = OllamaConfig::default();
        let messages = vec![Message::user("hello")];
        let gen_config = GenerationConfig {
            max_tokens: 512,
            temperature: 0.0,
            top_p: Some(0.95),
            top_k: Some(40),
            repeat_penalty: Some(1.1),
            seed: Some(42),
        };
        let body = build_request_body(&ollama_config, &messages, &[], &gen_config);

        assert_eq!(body["options"]["temperature"], 0.0);
        assert_eq!(body["options"]["num_predict"], 512);
        assert_eq!(body["options"]["top_p"], 0.95);
        assert_eq!(body["options"]["top_k"], 40);
        // f32 -> f64 conversion introduces minor floating point imprecision.
        let rp = body["options"]["repeat_penalty"].as_f64().unwrap();
        assert!((rp - 1.1).abs() < 1e-6);
        assert_eq!(body["options"]["seed"], 42);
    }

    #[test]
    fn transient_error_detection() {
        let timeout_err = anyhow::anyhow!("connection timed out");
        assert!(!is_transient(&timeout_err)); // String errors aren't reqwest errors

        let rate_err = anyhow::anyhow!("rate limited");
        assert!(is_transient(&rate_err));

        let parse_err = anyhow::anyhow!("invalid JSON");
        assert!(!is_transient(&parse_err));
    }
}
