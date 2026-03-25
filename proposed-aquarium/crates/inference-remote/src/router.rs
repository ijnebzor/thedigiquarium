use anyhow::Result;

use crate::client::RemoteClient;
use crate::provider::Provider;
use crate::stream::EventStream;
use crate::types::{ChatMessage, ChatResponse};

/// Routes requests across multiple providers with automatic fallback.
///
/// When a provider is rate-limited (429 or tracked as exhausted), the router
/// skips it and tries the next one. Providers are tried in the order given.
pub struct ProviderRouter {
    clients: Vec<RemoteClient>,
}

/// Which provider handled the request.
#[derive(Debug)]
pub struct RoutedResponse {
    pub provider: Provider,
    pub model: String,
    pub response: ChatResponse,
}

impl ProviderRouter {
    /// Create a router from a list of (provider, model) pairs.
    ///
    /// Each provider's API key is read from its environment variable.
    /// Providers that fail to initialise (e.g. missing API key) are skipped
    /// with a warning, allowing partial configuration.
    pub fn new(providers: Vec<(Provider, Option<&str>)>) -> Result<Self> {
        let mut clients = Vec::new();
        for (provider, model) in providers {
            match RemoteClient::new(provider, model) {
                Ok(client) => clients.push(client),
                Err(e) => {
                    tracing::warn!(provider = %provider, "skipping provider: {e}");
                }
            }
        }
        if clients.is_empty() {
            anyhow::bail!("no providers available — check API key environment variables");
        }
        Ok(Self { clients })
    }

    /// Create a router from pre-built clients.
    pub fn from_clients(clients: Vec<RemoteClient>) -> Result<Self> {
        if clients.is_empty() {
            anyhow::bail!("no providers available");
        }
        Ok(Self { clients })
    }

    /// How many providers are configured.
    pub fn provider_count(&self) -> usize {
        self.clients.len()
    }

    /// List configured providers and their models.
    pub fn providers(&self) -> Vec<(Provider, &str)> {
        self.clients
            .iter()
            .map(|c| (c.provider(), c.model()))
            .collect()
    }

    /// Send a chat completion, falling back through providers on rate limits.
    pub async fn chat(&self, messages: &[ChatMessage]) -> Result<RoutedResponse> {
        let mut last_err = None;

        for client in &self.clients {
            if !client.rate_limits.is_available(&client.provider()) {
                tracing::debug!(provider = %client.provider(), "skipping: rate limited");
                continue;
            }

            match client.chat(messages).await {
                Ok(response) => {
                    return Ok(RoutedResponse {
                        provider: client.provider(),
                        model: client.model().to_string(),
                        response,
                    });
                }
                Err(e) => {
                    tracing::warn!(
                        provider = %client.provider(),
                        "request failed, trying next: {e}"
                    );
                    last_err = Some(e);
                }
            }
        }

        Err(last_err.unwrap_or_else(|| anyhow::anyhow!("all providers exhausted")))
    }

    /// Send a chat completion with tools, falling back on rate limits.
    pub async fn chat_with_tools(
        &self,
        messages: &[ChatMessage],
        tools: &[aquarium_core::Tool],
    ) -> Result<RoutedResponse> {
        let mut last_err = None;

        for client in &self.clients {
            if !client.rate_limits.is_available(&client.provider()) {
                tracing::debug!(provider = %client.provider(), "skipping: rate limited");
                continue;
            }

            match client.chat_with_tools(messages, tools).await {
                Ok(response) => {
                    return Ok(RoutedResponse {
                        provider: client.provider(),
                        model: client.model().to_string(),
                        response,
                    });
                }
                Err(e) => {
                    tracing::warn!(
                        provider = %client.provider(),
                        "request failed, trying next: {e}"
                    );
                    last_err = Some(e);
                }
            }
        }

        Err(last_err.unwrap_or_else(|| anyhow::anyhow!("all providers exhausted")))
    }

    /// Send a streaming request, falling back on rate limits.
    ///
    /// Returns the stream from the first available provider.
    pub async fn chat_stream(
        &self,
        messages: &[ChatMessage],
    ) -> Result<(Provider, EventStream)> {
        let mut last_err = None;

        for client in &self.clients {
            if !client.rate_limits.is_available(&client.provider()) {
                tracing::debug!(provider = %client.provider(), "skipping: rate limited");
                continue;
            }

            match client.chat_stream(messages).await {
                Ok(stream) => return Ok((client.provider(), stream)),
                Err(e) => {
                    tracing::warn!(
                        provider = %client.provider(),
                        "stream request failed, trying next: {e}"
                    );
                    last_err = Some(e);
                }
            }
        }

        Err(last_err.unwrap_or_else(|| anyhow::anyhow!("all providers exhausted")))
    }
}
