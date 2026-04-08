//! inference-local — Track 1: Local inference on Metal
//!
//! Two backends for running inference on the local machine:
//!
//! - **Ollama/LM Studio** ([`OllamaBackend`]): HTTP client connecting to localhost:11434
//!   via `/api/chat`. Supports native tool calling for Qwen3-0.6B, LFM2.5-1.2B, etc.
//!
//! - **Candle on Metal** ([`CandleBackend`]): Loads GGUF quantized models via
//!   candle-transformers, runs inference on Apple GPU. Starts with Qwen3-0.6B.
//!
//! Both implement [`aquarium_core::InferenceProvider`].

pub mod candle_backend;
pub mod ollama;

pub use candle_backend::CandleBackend;
pub use ollama::OllamaBackend;

// Re-export core types for convenience.
pub use aquarium_core::{
    Completion, FinishReason, GenerationConfig, InferenceProvider, Message, Role, Tool, ToolCall,
    Usage,
};

use aquarium_core::specimen::InferenceBackend;

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/// Construct a local inference backend from a specimen's configuration.
///
/// Returns a boxed trait object suitable for use in the specimen loop.
///
/// - `InferenceBackend::LocalHttp` → [`OllamaBackend`] (runs health check)
/// - `InferenceBackend::Candle` → [`CandleBackend`] (downloads + loads model)
/// - `InferenceBackend::Remote` → error (handled by inference-remote crate)
pub async fn build_local_provider(
    backend: &InferenceBackend,
) -> anyhow::Result<Box<dyn InferenceProvider>> {
    match backend {
        InferenceBackend::LocalHttp { base_url, model } => {
            let config = ollama::OllamaConfig {
                base_url: base_url.clone(),
                model: model.clone(),
                ..ollama::OllamaConfig::default()
            };
            let backend = ollama::OllamaBackend::new(config)?;
            backend.health_check().await?;
            Ok(Box::new(backend))
        }
        InferenceBackend::Candle {
            model_id,
            quantization,
        } => {
            let config =
                candle_backend::CandleConfig::from_model_id(model_id, quantization.as_deref());
            let backend = tokio::task::spawn_blocking(move || {
                candle_backend::CandleBackend::load(config)
            })
            .await
            .map_err(|e| anyhow::anyhow!("Model loading task panicked: {e}"))??;
            Ok(Box::new(backend))
        }
        InferenceBackend::Remote { .. } => {
            anyhow::bail!("Remote backends should be constructed via the inference-remote crate")
        }
    }
}

// ---------------------------------------------------------------------------
// Tool call parsing (shared by Candle backend and any text-output backend)
// ---------------------------------------------------------------------------

/// Parse tool calls from generated text.
///
/// Handles multiple formats with priority ordering:
/// 1. Qwen3 native: `<tool_call>{"name": "...", "arguments": {...}}</tool_call>`
/// 2. Prompt-injected: ````json\n{"tool": "...", "arguments": {...}}\n````
/// 3. Inline JSON: `{"tool": "...", "arguments": {...}}`
pub fn parse_tool_calls(text: &str) -> Vec<ToolCall> {
    let mut calls = Vec::new();

    // Format 1: Qwen3 native <tool_call>...</tool_call>
    for segment in text.split("<tool_call>").skip(1) {
        if let Some(json_str) = segment.split("</tool_call>").next() {
            if let Some(call) = try_parse_tool_call(json_str.trim()) {
                calls.push(call);
            }
        }
    }
    if !calls.is_empty() {
        return calls;
    }

    // Format 2: ```json ... ```
    for segment in text.split("```json").skip(1) {
        if let Some(json_str) = segment.split("```").next() {
            if let Some(call) = try_parse_tool_call(json_str.trim()) {
                calls.push(call);
            }
        }
    }
    if !calls.is_empty() {
        return calls;
    }

    // Format 3: Inline JSON — find ALL occurrences by advancing the search position.
    let mut search_pos = 0;
    while search_pos < text.len() {
        let remaining = &text[search_pos..];

        // Find the earliest occurrence of either pattern.
        let next_match = ["{\"tool\"", "{\"name\""]
            .iter()
            .filter_map(|p| remaining.find(p))
            .min();

        match next_match {
            Some(offset) => {
                if let Some(json_str) = extract_json_object(&remaining[offset..]) {
                    if let Some(call) = try_parse_tool_call(json_str) {
                        calls.push(call);
                    }
                    search_pos += offset + json_str.len();
                } else {
                    search_pos += offset + 1;
                }
            }
            None => break,
        }
    }

    calls
}

fn try_parse_tool_call(json_str: &str) -> Option<ToolCall> {
    let val: serde_json::Value = serde_json::from_str(json_str).ok()?;

    // {"tool": "name", "arguments": {...}}
    if let (Some(tool), Some(args)) = (
        val.get("tool").and_then(|v| v.as_str()),
        val.get("arguments"),
    ) {
        return Some(ToolCall {
            id: None,
            tool: tool.to_string(),
            arguments: args.clone(),
        });
    }

    // {"name": "name", "arguments": {...}}
    if let (Some(name), Some(args)) = (
        val.get("name").and_then(|v| v.as_str()),
        val.get("arguments"),
    ) {
        return Some(ToolCall {
            id: None,
            tool: name.to_string(),
            arguments: args.clone(),
        });
    }

    None
}

/// Extract a JSON object from text, handling nested braces and string escaping.
fn extract_json_object(text: &str) -> Option<&str> {
    if !text.starts_with('{') {
        return None;
    }
    let mut depth = 0i32;
    let mut in_string = false;
    let mut escape = false;

    for (i, ch) in text.char_indices() {
        if escape {
            escape = false;
            continue;
        }
        match ch {
            '\\' if in_string => escape = true,
            '"' => in_string = !in_string,
            '{' if !in_string => depth += 1,
            '}' if !in_string => {
                depth -= 1;
                if depth == 0 {
                    return Some(&text[..=i]);
                }
            }
            _ => {}
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Format 1: Qwen3 native ---

    #[test]
    fn parse_qwen3_tool_call() {
        let text = r#"I'd like to search for that. <tool_call>
{"name": "search", "arguments": {"query": "music mathematics"}}
</tool_call>"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].tool, "search");
        assert_eq!(calls[0].arguments["query"], "music mathematics");
        assert!(calls[0].id.is_none());
    }

    #[test]
    fn parse_multiple_qwen3_tool_calls() {
        let text = r#"<tool_call>{"name": "search", "arguments": {"query": "a"}}</tool_call>
and then <tool_call>{"name": "read", "arguments": {"title": "b"}}</tool_call>"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 2);
        assert_eq!(calls[0].tool, "search");
        assert_eq!(calls[1].tool, "read");
    }

    // --- Format 2: JSON block ---

    #[test]
    fn parse_json_block_tool_call() {
        let text = "Let me search for that.\n\n```json\n{\"tool\": \"search\", \"arguments\": {\"query\": \"pythagorean tuning\"}}\n```";
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].tool, "search");
    }

    // --- Format 3: Inline JSON ---

    #[test]
    fn parse_inline_tool_call() {
        let text = r#"{"tool": "read", "arguments": {"title": "Music and Mathematics"}}"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].tool, "read");
    }

    #[test]
    fn parse_multiple_inline_tool_calls() {
        let text = r#"First: {"tool": "search", "arguments": {"query": "music"}} then {"tool": "read", "arguments": {"title": "Music"}}"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 2);
        assert_eq!(calls[0].tool, "search");
        assert_eq!(calls[1].tool, "read");
    }

    // --- Edge cases ---

    #[test]
    fn no_tool_calls_in_plain_text() {
        let text = "I find this topic fascinating. The relationship between harmony and ratios...";
        let calls = parse_tool_calls(text);
        assert!(calls.is_empty());
    }

    #[test]
    fn malformed_json_in_qwen3_tag() {
        let text = r#"<tool_call>{"name": broken json</tool_call>"#;
        let calls = parse_tool_calls(text);
        assert!(calls.is_empty());
    }

    #[test]
    fn nested_braces_in_arguments() {
        let text = r#"{"tool": "search", "arguments": {"query": "test {with} braces"}}"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].arguments["query"], "test {with} braces");
    }

    #[test]
    fn escaped_quotes_in_arguments() {
        let text = r#"{"tool": "search", "arguments": {"query": "say \"hello\""}}"#;
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].arguments["query"], "say \"hello\"");
    }

    #[test]
    fn partial_tool_call_tag() {
        let text = r#"<tool_call>{"name": "search", "arguments": {"query": "test"}}"#;
        // Missing </tool_call> — the split("</tool_call>").next() returns the rest
        // of the string, but JSON parsing should still work since it's valid JSON.
        let calls = parse_tool_calls(text);
        assert_eq!(calls.len(), 1);
    }

    #[test]
    fn json_without_tool_or_name_key() {
        let text = r#"{"action": "search", "arguments": {"query": "test"}}"#;
        let calls = parse_tool_calls(text);
        assert!(calls.is_empty());
    }

    #[test]
    fn empty_string() {
        assert!(parse_tool_calls("").is_empty());
    }
}
