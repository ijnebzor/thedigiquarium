use anyhow::Result;

use crate::types::{StreamChunk, StreamDelta, TokenUsage};

/// An SSE event stream from a chat completion endpoint.
///
/// Wraps a `reqwest::Response` and parses `data:` events incrementally.
/// Call `next_delta()` repeatedly until it returns `Ok(None)`.
pub struct EventStream {
    response: reqwest::Response,
    buffer: String,
}

impl EventStream {
    pub(crate) fn new(response: reqwest::Response) -> Self {
        Self {
            response,
            buffer: String::new(),
        }
    }

    /// Read the next delta from the stream.
    ///
    /// Returns `Ok(None)` when the stream is complete (`[DONE]` or EOF).
    pub async fn next_delta(&mut self) -> Result<Option<StreamDelta>> {
        loop {
            // Try to extract a complete SSE event (terminated by blank line).
            if let Some(event) = self.extract_event() {
                match self.parse_event(&event)? {
                    EventResult::Delta(delta) => return Ok(Some(delta)),
                    EventResult::Done => return Ok(None),
                    EventResult::Skip => continue,
                }
            }

            // Read more data from the response body.
            match self.response.chunk().await? {
                Some(bytes) => {
                    self.buffer.push_str(&String::from_utf8_lossy(&bytes));
                }
                None => return Ok(None),
            }
        }
    }

    /// Collect the entire stream into a single `ChatResponse`-style result.
    ///
    /// Concatenates content deltas and assembles tool calls by index.
    pub async fn collect(mut self) -> Result<CollectedStream> {
        let mut content = String::new();
        let mut tool_calls: Vec<ToolCallAccumulator> = Vec::new();
        let mut finish_reason = None;
        let mut usage = None;

        while let Some(delta) = self.next_delta().await? {
            if let Some(text) = &delta.content {
                content.push_str(text);
            }

            if let Some(tc_deltas) = &delta.tool_calls {
                for tc in tc_deltas {
                    // Grow the accumulator vec as needed.
                    let idx = tc.index as usize;
                    if tool_calls.len() <= idx {
                        tool_calls.resize_with(idx + 1, ToolCallAccumulator::default);
                    }
                    let acc = &mut tool_calls[idx];
                    if let Some(id) = &tc.id {
                        acc.id = Some(id.clone());
                    }
                    if let Some(f) = &tc.function {
                        if let Some(name) = &f.name {
                            acc.name = Some(name.clone());
                        }
                        if let Some(args) = &f.arguments {
                            acc.arguments.push_str(args);
                        }
                    }
                }
            }

            if delta.finish_reason.is_some() {
                finish_reason = delta.finish_reason;
            }
            if delta.usage.is_some() {
                usage = delta.usage;
            }
        }

        Ok(CollectedStream {
            content: if content.is_empty() {
                None
            } else {
                Some(content)
            },
            tool_calls: tool_calls
                .into_iter()
                .filter_map(|acc| acc.into_parsed())
                .collect(),
            finish_reason,
            usage,
        })
    }

    /// Try to extract one complete SSE event from the buffer.
    fn extract_event(&mut self) -> Option<String> {
        // SSE events are separated by a blank line (\n\n).
        let pos = self.buffer.find("\n\n")?;
        let event = self.buffer[..pos].to_string();
        self.buffer = self.buffer[pos + 2..].to_string();
        Some(event)
    }

    fn parse_event(&self, event: &str) -> Result<EventResult> {
        for line in event.lines() {
            let data = match line.strip_prefix("data:") {
                Some(d) => d.trim(),
                None => continue,
            };

            if data == "[DONE]" {
                return Ok(EventResult::Done);
            }

            if data.is_empty() {
                continue;
            }

            let chunk: StreamChunk = serde_json::from_str(data)?;
            let choice = match chunk.choices.into_iter().next() {
                Some(c) => c,
                None => return Ok(EventResult::Skip),
            };

            return Ok(EventResult::Delta(StreamDelta {
                content: choice.delta.content,
                tool_calls: choice.delta.tool_calls,
                finish_reason: choice.finish_reason,
                usage: chunk.usage,
            }));
        }

        Ok(EventResult::Skip)
    }
}

enum EventResult {
    Delta(StreamDelta),
    Done,
    Skip,
}

/// Result of collecting an entire SSE stream.
#[derive(Debug)]
pub struct CollectedStream {
    pub content: Option<String>,
    pub tool_calls: Vec<crate::types::ToolCallParsed>,
    pub finish_reason: Option<String>,
    pub usage: Option<TokenUsage>,
}

#[derive(Debug, Default)]
struct ToolCallAccumulator {
    id: Option<String>,
    name: Option<String>,
    arguments: String,
}

impl ToolCallAccumulator {
    fn into_parsed(self) -> Option<crate::types::ToolCallParsed> {
        let id = self.id?;
        let name = self.name?;
        let arguments = serde_json::from_str(&self.arguments).unwrap_or(serde_json::Value::Null);
        Some(crate::types::ToolCallParsed {
            id,
            name,
            arguments,
        })
    }
}
