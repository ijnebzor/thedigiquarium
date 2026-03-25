use std::future::Future;
use std::pin::Pin;

use serde::{Deserialize, Serialize};

use crate::tool::{Tool, ToolCall};

// ---------------------------------------------------------------------------
// Message types
// ---------------------------------------------------------------------------

/// Role in a conversation message.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    System,
    User,
    Assistant,
    Tool,
}

/// A single message in a conversation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: String,
}

impl Message {
    pub fn system(content: impl Into<String>) -> Self {
        Self { role: Role::System, content: content.into() }
    }

    pub fn user(content: impl Into<String>) -> Self {
        Self { role: Role::User, content: content.into() }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self { role: Role::Assistant, content: content.into() }
    }

    pub fn tool(content: impl Into<String>) -> Self {
        Self { role: Role::Tool, content: content.into() }
    }
}

// ---------------------------------------------------------------------------
// Completion response
// ---------------------------------------------------------------------------

/// Result of an inference completion.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Completion {
    pub content: String,
    pub tool_calls: Vec<ToolCall>,
    pub usage: Option<Usage>,
    pub finish_reason: FinishReason,
}

/// Why generation stopped.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FinishReason {
    /// Model produced an end-of-sequence token.
    Stop,
    /// Hit the maximum token limit (response may be truncated).
    MaxTokens,
    /// Model produced one or more tool calls.
    ToolCall,
}

/// Token usage statistics from inference.
#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
pub struct Usage {
    pub prompt_tokens: Option<u32>,
    pub completion_tokens: Option<u32>,
}

// ---------------------------------------------------------------------------
// Generation configuration
// ---------------------------------------------------------------------------

/// Parameters controlling text generation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationConfig {
    /// Maximum tokens to generate.
    pub max_tokens: u32,
    /// Sampling temperature (0.0 = greedy).
    pub temperature: f64,
    /// Top-p (nucleus) sampling threshold.
    pub top_p: Option<f64>,
    /// Top-k sampling (select from top k tokens).
    pub top_k: Option<usize>,
    /// Penalise repeated tokens.
    pub repeat_penalty: Option<f32>,
    /// Random seed for reproducible sampling.
    pub seed: Option<u64>,
}

impl Default for GenerationConfig {
    fn default() -> Self {
        Self {
            max_tokens: 1024,
            temperature: 0.7,
            top_p: Some(0.9),
            top_k: None,
            repeat_penalty: None,
            seed: None,
        }
    }
}

// ---------------------------------------------------------------------------
// Trait
// ---------------------------------------------------------------------------

/// Common interface for all inference backends.
///
/// The specimen loop uses this trait to generate completions regardless of
/// whether inference happens via HTTP (Ollama), in-process (Candle), or
/// remote API (Groq, Gemini, etc.).
///
/// Object-safe so the loop can hold `Box<dyn InferenceProvider>`.
pub trait InferenceProvider: Send + Sync {
    /// Generate a completion from a conversation.
    ///
    /// `messages` contains the full conversation history (system + user + assistant turns).
    /// `tools` lists available tools — backends with native tool support pass them to the
    /// model directly; others ignore them (expect tool descriptions in the system prompt
    /// via `aquarium_core::prompt::tools_as_prompt_text()`).
    /// `config` controls generation parameters (temperature, max_tokens, etc.).
    fn complete(
        &self,
        messages: &[Message],
        tools: &[Tool],
        config: &GenerationConfig,
    ) -> Pin<Box<dyn Future<Output = anyhow::Result<Completion>> + Send + '_>>;

    /// Human-readable backend name for logging (e.g. "ollama/qwen3-0.6b").
    fn name(&self) -> &str;

    /// Whether this backend supports passing tools natively to the model.
    ///
    /// If `false`, callers should inject tool descriptions into the system prompt
    /// using `aquarium_core::prompt::tools_as_prompt_text()`.
    fn supports_native_tools(&self) -> bool;
}
