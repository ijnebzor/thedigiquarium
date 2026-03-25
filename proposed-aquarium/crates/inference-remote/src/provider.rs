use serde::{Deserialize, Serialize};
use std::fmt;

/// A supported remote inference provider.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Provider {
    Groq,
    Cerebras,
    GoogleAIStudio,
    Mistral,
    OpenRouter,
    GitHubModels,
    #[serde(rename = "xai")]
    XAI,
    DeepSeek,
    SambaNova,
}

impl fmt::Display for Provider {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Groq => write!(f, "Groq"),
            Self::Cerebras => write!(f, "Cerebras"),
            Self::GoogleAIStudio => write!(f, "Google AI Studio"),
            Self::Mistral => write!(f, "Mistral"),
            Self::OpenRouter => write!(f, "OpenRouter"),
            Self::GitHubModels => write!(f, "GitHub Models"),
            Self::XAI => write!(f, "xAI"),
            Self::DeepSeek => write!(f, "DeepSeek"),
            Self::SambaNova => write!(f, "SambaNova"),
        }
    }
}

/// Static configuration for a provider — base URL, env var for API key, defaults.
#[derive(Debug, Clone)]
pub struct ProviderConfig {
    pub provider: Provider,
    pub base_url: &'static str,
    pub api_key_env: &'static str,
    pub default_model: &'static str,
    pub supports_tools: bool,
    pub supports_streaming: bool,
}

impl Provider {
    /// Return the static configuration for this provider.
    pub fn config(self) -> ProviderConfig {
        match self {
            Self::Groq => ProviderConfig {
                provider: self,
                base_url: "https://api.groq.com/openai/v1",
                api_key_env: "GROQ_API_KEY",
                default_model: "llama-3.3-70b-versatile",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::Cerebras => ProviderConfig {
                provider: self,
                base_url: "https://api.cerebras.ai/v1",
                api_key_env: "CEREBRAS_API_KEY",
                default_model: "llama-3.3-70b",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::GoogleAIStudio => ProviderConfig {
                provider: self,
                base_url: "https://generativelanguage.googleapis.com/v1beta/openai",
                api_key_env: "GOOGLE_AI_API_KEY",
                default_model: "gemini-2.5-flash",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::Mistral => ProviderConfig {
                provider: self,
                base_url: "https://api.mistral.ai/v1",
                api_key_env: "MISTRAL_API_KEY",
                default_model: "mistral-large-latest",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::OpenRouter => ProviderConfig {
                provider: self,
                base_url: "https://openrouter.ai/api/v1",
                api_key_env: "OPENROUTER_API_KEY",
                default_model: "meta-llama/llama-3.3-70b-instruct:free",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::GitHubModels => ProviderConfig {
                provider: self,
                base_url: "https://models.inference.ai.azure.com",
                api_key_env: "GITHUB_TOKEN",
                default_model: "gpt-4o",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::XAI => ProviderConfig {
                provider: self,
                base_url: "https://api.x.ai/v1",
                api_key_env: "XAI_API_KEY",
                default_model: "grok-3-mini",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::DeepSeek => ProviderConfig {
                provider: self,
                base_url: "https://api.deepseek.com",
                api_key_env: "DEEPSEEK_API_KEY",
                default_model: "deepseek-chat",
                supports_tools: true,
                supports_streaming: true,
            },
            Self::SambaNova => ProviderConfig {
                provider: self,
                base_url: "https://api.sambanova.ai/v1",
                api_key_env: "SAMBANOVA_API_KEY",
                default_model: "Meta-Llama-3.3-70B-Instruct",
                supports_tools: true,
                supports_streaming: true,
            },
        }
    }

    /// All available providers.
    pub fn all() -> &'static [Provider] {
        &[
            Self::Groq,
            Self::Cerebras,
            Self::GoogleAIStudio,
            Self::Mistral,
            Self::OpenRouter,
            Self::GitHubModels,
            Self::XAI,
            Self::DeepSeek,
            Self::SambaNova,
        ]
    }

    /// Parse a provider name (case-insensitive).
    pub fn from_name(name: &str) -> Option<Self> {
        match name.to_lowercase().as_str() {
            "groq" => Some(Self::Groq),
            "cerebras" => Some(Self::Cerebras),
            "google" | "google_ai_studio" | "googleaistudio" | "gemini" => {
                Some(Self::GoogleAIStudio)
            }
            "mistral" => Some(Self::Mistral),
            "openrouter" | "open_router" => Some(Self::OpenRouter),
            "github" | "github_models" | "githubmodels" => Some(Self::GitHubModels),
            "xai" | "grok" => Some(Self::XAI),
            "deepseek" => Some(Self::DeepSeek),
            "sambanova" => Some(Self::SambaNova),
            _ => None,
        }
    }
}

impl ProviderConfig {
    /// Read the API key from the environment variable.
    pub fn api_key(&self) -> anyhow::Result<String> {
        std::env::var(self.api_key_env).map_err(|_| {
            anyhow::anyhow!(
                "{}: set {} environment variable",
                self.provider,
                self.api_key_env,
            )
        })
    }
}
