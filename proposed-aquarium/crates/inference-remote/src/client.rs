use std::future::Future;
use std::pin::Pin;

use anyhow::{Context, Result};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};

use aquarium_core::inference::{
    Completion, FinishReason, GenerationConfig, InferenceProvider, Message, Usage,
};
use aquarium_core::tool::{Tool, ToolCall};

use crate::provider::{Provider, ProviderConfig};
use crate::rate_limit::RateLimitTracker;
use crate::stream::EventStream;
use crate::types::{
    ChatMessage, ChatResponse, CompletionRequest, CompletionResponse, ToolCallParsed,
    ToolDefinition,
};

/// An OpenAI-compatible HTTP client for a single remote provider.
pub struct RemoteClient {
    http: reqwest::Client,
    config: ProviderConfig,
    /// Resolved base URL (may differ from config.base_url if overridden via from_parts).
    base_url: String,
    model: String,
    api_key: String,
    pub(crate) rate_limits: RateLimitTracker,
}

impl RemoteClient {
    /// Create a client for the given provider and model.
    ///
    /// Reads the API key from the provider's environment variable.
    /// Pass `None` for model to use the provider's default.
    pub fn new(provider: Provider, model: Option<&str>) -> Result<Self> {
        let config = provider.config();
        let api_key = config.api_key()?.trim().to_string();
        let base_url = config.base_url.to_string();
        let model = model
            .unwrap_or(config.default_model)
            .to_string();

        Ok(Self {
            http: reqwest::Client::new(),
            config,
            base_url,
            model,
            api_key,
            rate_limits: RateLimitTracker::new(),
        })
    }

    /// Create a client from explicit configuration values.
    pub fn from_parts(
        provider: Provider,
        base_url: String,
        model: String,
        api_key: String,
    ) -> Self {
        let config = provider.config();

        Self {
            http: reqwest::Client::new(),
            config,
            base_url,
            model,
            api_key: api_key.trim().to_string(),
            rate_limits: RateLimitTracker::new(),
        }
    }

    pub fn provider(&self) -> Provider {
        self.config.provider
    }

    pub fn model(&self) -> &str {
        &self.model
    }

    /// Send a chat completion request and return the parsed response.
    pub async fn chat(&self, messages: &[ChatMessage]) -> Result<ChatResponse> {
        self.chat_inner(messages, None).await
    }

    /// Send a chat completion request with tool definitions.
    pub async fn chat_with_tools(
        &self,
        messages: &[ChatMessage],
        tools: &[aquarium_core::Tool],
    ) -> Result<ChatResponse> {
        let tool_defs: Vec<ToolDefinition> = tools.iter().map(ToolDefinition::from).collect();
        self.chat_inner(messages, Some(tool_defs)).await
    }

    /// Send a streaming chat completion request.
    ///
    /// Returns an `EventStream` that yields deltas incrementally.
    pub async fn chat_stream(&self, messages: &[ChatMessage]) -> Result<EventStream> {
        self.stream_inner(messages, None).await
    }

    /// Send a streaming chat completion with tool definitions.
    pub async fn chat_stream_with_tools(
        &self,
        messages: &[ChatMessage],
        tools: &[aquarium_core::Tool],
    ) -> Result<EventStream> {
        let tool_defs: Vec<ToolDefinition> = tools.iter().map(ToolDefinition::from).collect();
        self.stream_inner(messages, Some(tool_defs)).await
    }

    // ── Internal ────────────────────────────────────────────────────────────

    async fn chat_inner(
        &self,
        messages: &[ChatMessage],
        tools: Option<Vec<ToolDefinition>>,
    ) -> Result<ChatResponse> {
        let body = CompletionRequest {
            model: self.model.clone(),
            messages: messages.to_vec(),
            tools,
            stream: None,
            temperature: None,
            max_tokens: None,
        };

        let url = format!("{}/chat/completions", self.base_url);
        tracing::debug!(provider = %self.config.provider, model = %self.model, "chat completion");

        let response = self
            .http
            .post(&url)
            .headers(self.auth_headers()?)
            .json(&body)
            .send()
            .await
            .context("HTTP request failed")?;

        // Update rate limit tracking from response headers.
        self.rate_limits
            .update_from_headers(&self.config.provider, response.headers());

        let status = response.status();
        if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
            // 429 — mark provider as rate-limited.
            self.rate_limits.mark_rate_limited(
                &self.config.provider,
                std::time::Duration::from_secs(60),
            );
            anyhow::bail!(
                "{}: rate limited (429) on model {}",
                self.config.provider,
                self.model,
            );
        }

        let body_text = response
            .text()
            .await
            .context("failed to read response body")?;

        if !status.is_success() {
            anyhow::bail!(
                "{}: HTTP {} — {}",
                self.config.provider,
                status,
                body_text,
            );
        }

        let raw: CompletionResponse = serde_json::from_str(&body_text)
            .with_context(|| {
                format!(
                    "{}: failed to parse response: {}",
                    self.config.provider, body_text
                )
            })?;

        Ok(parse_completion_response(raw))
    }

    async fn stream_inner(
        &self,
        messages: &[ChatMessage],
        tools: Option<Vec<ToolDefinition>>,
    ) -> Result<EventStream> {
        let body = CompletionRequest {
            model: self.model.clone(),
            messages: messages.to_vec(),
            tools,
            stream: Some(true),
            temperature: None,
            max_tokens: None,
        };

        let url = format!("{}/chat/completions", self.base_url);
        tracing::debug!(provider = %self.config.provider, model = %self.model, "streaming chat");

        let response = self
            .http
            .post(&url)
            .headers(self.auth_headers()?)
            .json(&body)
            .send()
            .await
            .context("HTTP request failed")?;

        self.rate_limits
            .update_from_headers(&self.config.provider, response.headers());

        let status = response.status();
        if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
            self.rate_limits.mark_rate_limited(
                &self.config.provider,
                std::time::Duration::from_secs(60),
            );
            anyhow::bail!(
                "{}: rate limited (429) on model {}",
                self.config.provider,
                self.model,
            );
        }

        if !status.is_success() {
            let body_text = response.text().await.unwrap_or_default();
            anyhow::bail!(
                "{}: HTTP {} — {}",
                self.config.provider,
                status,
                body_text,
            );
        }

        Ok(EventStream::new(response))
    }

    fn auth_headers(&self) -> Result<HeaderMap> {
        let mut headers = HeaderMap::new();
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(&format!("Bearer {}", self.api_key))
                .map_err(|e| anyhow::anyhow!("invalid API key (non-ASCII characters?): {e}"))?,
        );
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        Ok(headers)
    }
}

// ---------------------------------------------------------------------------
// InferenceProvider trait — bridges aquarium-core types to the remote client.
// ---------------------------------------------------------------------------

impl InferenceProvider for RemoteClient {
    fn complete(
        &self,
        messages: &[Message],
        tools: &[Tool],
        config: &GenerationConfig,
    ) -> Pin<Box<dyn Future<Output = Result<Completion>> + Send + '_>> {
        let chat_messages: Vec<ChatMessage> = messages
            .iter()
            .map(|m| ChatMessage {
                role: match m.role {
                    aquarium_core::Role::System => "system".into(),
                    aquarium_core::Role::User => "user".into(),
                    aquarium_core::Role::Assistant => "assistant".into(),
                    aquarium_core::Role::Tool => "tool".into(),
                },
                content: Some(m.content.clone()),
                tool_calls: None,
                tool_call_id: None,
            })
            .collect();
        let tool_defs: Option<Vec<ToolDefinition>> = if tools.is_empty() {
            None
        } else {
            Some(tools.iter().map(ToolDefinition::from).collect())
        };
        let temperature = Some(config.temperature as f32);
        let max_tokens = Some(config.max_tokens);

        Box::pin(async move {
            let body = CompletionRequest {
                model: self.model.clone(),
                messages: chat_messages,
                tools: tool_defs,
                stream: None,
                temperature,
                max_tokens,
            };

            let url = format!("{}/chat/completions", self.base_url);
            tracing::debug!(
                provider = %self.config.provider,
                model = %self.model,
                "InferenceProvider::complete"
            );

            let response = self
                .http
                .post(&url)
                .headers(self.auth_headers()?)
                .json(&body)
                .send()
                .await
                .context("HTTP request failed")?;

            self.rate_limits
                .update_from_headers(&self.config.provider, response.headers());

            let status = response.status();
            if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
                self.rate_limits.mark_rate_limited(
                    &self.config.provider,
                    std::time::Duration::from_secs(60),
                );
                anyhow::bail!(
                    "{}: rate limited (429) on model {}",
                    self.config.provider,
                    self.model,
                );
            }

            let body_text = response.text().await.context("failed to read response body")?;
            if !status.is_success() {
                anyhow::bail!("{}: HTTP {} — {}", self.config.provider, status, body_text);
            }

            let raw: CompletionResponse =
                serde_json::from_str(&body_text).with_context(|| {
                    format!("{}: failed to parse response: {}", self.config.provider, body_text)
                })?;

            let chat_resp = parse_completion_response(raw);

            // Convert ChatResponse → aquarium_core::Completion
            let tool_calls: Vec<ToolCall> = chat_resp
                .tool_calls
                .into_iter()
                .map(|tc| ToolCall {
                    id: Some(tc.id),
                    tool: tc.name,
                    arguments: tc.arguments,
                })
                .collect();

            let finish_reason = match chat_resp.finish_reason.as_deref() {
                Some("tool_calls") => FinishReason::ToolCall,
                Some("length") => FinishReason::MaxTokens,
                _ => FinishReason::Stop,
            };

            let usage = chat_resp.usage.map(|u| Usage {
                prompt_tokens: Some(u.prompt_tokens),
                completion_tokens: Some(u.completion_tokens),
            });

            Ok(Completion {
                content: chat_resp.content.unwrap_or_default(),
                tool_calls,
                usage,
                finish_reason,
            })
        })
    }

    fn name(&self) -> &str {
        &self.model
    }

    fn supports_native_tools(&self) -> bool {
        self.config.supports_tools
    }
}

/// Parse the raw API response into our public `ChatResponse` type.
fn parse_completion_response(raw: CompletionResponse) -> ChatResponse {
    let choice = raw.choices.into_iter().next();

    let (content, raw_tool_calls, finish_reason) = match choice {
        Some(c) => (
            c.message.content,
            c.message.tool_calls.unwrap_or_default(),
            c.finish_reason,
        ),
        None => (None, Vec::new(), None),
    };

    let tool_calls: Vec<ToolCallParsed> = raw_tool_calls
        .into_iter()
        .map(|tc| ToolCallParsed {
            id: tc.id,
            name: tc.function.name,
            arguments: serde_json::from_str(&tc.function.arguments)
                .unwrap_or(serde_json::Value::Null),
        })
        .collect();

    ChatResponse {
        content,
        tool_calls,
        usage: raw.usage,
        finish_reason,
    }
}
