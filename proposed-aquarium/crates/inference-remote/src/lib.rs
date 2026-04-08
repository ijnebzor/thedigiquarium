//! Unified OpenAI-compatible client for free remote inference providers.
//!
//! All supported providers use the OpenAI chat completions format, so a single
//! client implementation handles all of them by swapping `base_url` and `api_key`.
//!
//! # Providers
//!
//! | Provider | Free Tier | Best Model |
//! |----------|-----------|------------|
//! | Groq | 1,000 RPD | Llama 3.3 70B |
//! | Cerebras | 1M tok/day | Llama 3.3 70B |
//! | Google AI Studio | 250 RPD, 1M context | Gemini 2.5 Flash |
//! | Mistral | 2 RPM, 1B tok/mo | Mistral Large |
//! | OpenRouter | 200 RPD | ~30 free models |
//! | GitHub Models | 50 RPD | GPT-4o |
//! | xAI | $25 credits | Grok |
//! | DeepSeek | 5M tokens | DeepSeek Chat |
//! | SambaNova | 200K tok/day | Llama 3.3 70B |
//!
//! # Usage
//!
//! ```no_run
//! use inference_remote::{RemoteClient, Provider, ChatMessage};
//!
//! # async fn example() -> anyhow::Result<()> {
//! // Single provider
//! let client = RemoteClient::new(Provider::Groq, None)?;
//! let response = client.chat(&[
//!     ChatMessage::system("You are a helpful assistant."),
//!     ChatMessage::user("What is the speed of light?"),
//! ]).await?;
//! println!("{}", response.content.unwrap_or_default());
//!
//! // Multi-provider with fallback
//! use inference_remote::ProviderRouter;
//! let router = ProviderRouter::new(vec![
//!     (Provider::Groq, None),
//!     (Provider::Cerebras, None),
//!     (Provider::GoogleAIStudio, None),
//! ])?;
//! let routed = router.chat(&[ChatMessage::user("Hello!")]).await?;
//! println!("Handled by {} ({})", routed.provider, routed.model);
//! # Ok(())
//! # }
//! ```

pub mod client;
pub mod provider;
mod rate_limit;
pub mod router;
pub mod stream;
pub mod types;

// Re-export the primary public API.
pub use client::RemoteClient;
pub use provider::{Provider, ProviderConfig};
pub use router::{ProviderRouter, RoutedResponse};
pub use stream::{CollectedStream, EventStream};
pub use types::{
    ChatMessage, ChatResponse, StreamDelta, StreamToolCallDelta, ToolCallParsed, TokenUsage,
};
