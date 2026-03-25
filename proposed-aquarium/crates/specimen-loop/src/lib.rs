pub mod conversation;
pub mod intent;
pub mod prompts;
pub mod selection;
pub mod trace;

use anyhow::{Context, Result};
use aquarium_core::inference::{GenerationConfig, InferenceProvider, Usage};
use aquarium_core::SpecimenConfig;
use conversation::Conversation;
use knowledge::KnowledgeBase;
use trace::{Exchange, ThinkingTrace, TraceLogger};

/// Configuration for the specimen exploration loop.
pub struct LoopConfig {
    /// Maximum cycles (None = run forever).
    pub max_cycles: Option<u64>,
    /// Number of search results to present.
    pub top_k: usize,
    /// Max messages in conversation history.
    pub max_conversation_messages: usize,
    /// Directory for thinking trace JSONL files.
    pub trace_dir: std::path::PathBuf,
    /// Generation parameters for inference.
    pub generation: GenerationConfig,
}

impl Default for LoopConfig {
    fn default() -> Self {
        Self {
            max_cycles: None,
            top_k: 3,
            max_conversation_messages: 50,
            trace_dir: std::path::PathBuf::from("traces"),
            generation: GenerationConfig::default(),
        }
    }
}

/// The manufactured agentic loop for a single specimen.
pub struct SpecimenLoop {
    config: LoopConfig,
    specimen: SpecimenConfig,
    knowledge: KnowledgeBase,
    inference: Box<dyn InferenceProvider>,
    conversation: Conversation,
    trace_logger: TraceLogger,
    cycle_number: u64,
}

/// Outcome of a single exploration cycle.
#[derive(Debug)]
pub enum CycleOutcome {
    Completed {
        query: String,
        article_selected: Option<String>,
        reflection: String,
    },
    NoResults {
        query: String,
    },
}

impl SpecimenLoop {
    pub fn new(
        config: LoopConfig,
        specimen: SpecimenConfig,
        knowledge: KnowledgeBase,
        inference: Box<dyn InferenceProvider>,
    ) -> Result<Self> {
        let trace_logger = TraceLogger::open(&config.trace_dir, &specimen.id)?;
        let conversation =
            Conversation::new(&specimen.system_prompt, config.max_conversation_messages);

        tracing::info!(
            "specimen loop ready: id={}, inference={}",
            specimen.id,
            inference.name()
        );

        Ok(Self {
            config,
            specimen,
            knowledge,
            inference,
            conversation,
            trace_logger,
            cycle_number: 0,
        })
    }

    /// Run the loop until max_cycles or forever.
    pub async fn run(&mut self) -> Result<()> {
        loop {
            if let Some(max) = self.config.max_cycles {
                if self.cycle_number >= max {
                    tracing::info!(
                        "specimen {} completed {} cycles",
                        self.specimen.id,
                        self.cycle_number
                    );
                    break;
                }
            }

            match self.run_cycle().await {
                Ok(outcome) => {
                    tracing::info!(
                        "specimen {} cycle {}: {:?}",
                        self.specimen.id,
                        self.cycle_number,
                        outcome
                    );
                }
                Err(e) => {
                    tracing::error!(
                        "specimen {} cycle {} error: {e:#}",
                        self.specimen.id,
                        self.cycle_number,
                    );
                    tokio::time::sleep(std::time::Duration::from_secs(5)).await;
                }
            }

            self.cycle_number += 1;
        }

        Ok(())
    }

    /// Run a single exploration cycle.
    ///
    /// The manufactured loop never passes tools to the model — we drive the
    /// conversation externally. Tools are empty; the model just talks.
    async fn run_cycle(&mut self) -> Result<CycleOutcome> {
        let mut total_usage = Usage::default();
        let mut exchanges = Vec::new();
        let no_tools = []; // Manufactured loop: no native tool calling

        // Step 1: exploration prompt
        let prompt = if self.cycle_number == 0 {
            prompts::EXPLORATION_PROMPT
        } else {
            prompts::CONTINUATION_PROMPT
        };
        self.conversation.add_user(prompt);

        // Step 2: specimen responds with interest
        let interest = self
            .inference
            .complete(
                self.conversation.messages(),
                &no_tools,
                &self.config.generation,
            )
            .await
            .context("failed to get exploration interest")?;
        accumulate(&mut total_usage, &interest.usage);
        self.conversation.add_assistant(&interest.content);
        exchanges.push(Exchange {
            step: "exploration".into(),
            prompt: prompt.to_string(),
            response: interest.content.clone(),
        });

        // Step 3: extract search query
        let query = intent::extract_search_query(&interest.content);
        tracing::debug!("extracted query: {query:?}");

        // Step 4: search
        let results = self
            .knowledge
            .search(&query, self.config.top_k)
            .context("knowledge search failed")?;

        if results.is_empty() {
            self.conversation.add_user(prompts::NO_RESULTS_PROMPT);
            self.trace_logger.log(&ThinkingTrace {
                timestamp: chrono::Utc::now(),
                specimen_id: self.specimen.id.clone(),
                cycle_number: self.cycle_number,
                exchanges,
                query: query.clone(),
                articles_found: vec![],
                article_selected: None,
                reflection: String::new(),
                prompt_tokens: total_usage.prompt_tokens,
                completion_tokens: total_usage.completion_tokens,
            })?;
            return Ok(CycleOutcome::NoResults { query });
        }

        // Step 5: present results
        let result_entries: Vec<(&str, &str)> = results
            .iter()
            .map(|r| (r.title.as_str(), r.snippet.as_str()))
            .collect();
        let presentation = prompts::present_results(&result_entries);
        self.conversation.add_user(&presentation);

        let articles_found: Vec<String> = results.iter().map(|r| r.title.clone()).collect();

        // Step 6: get selection
        let selection_resp = self
            .inference
            .complete(
                self.conversation.messages(),
                &no_tools,
                &self.config.generation,
            )
            .await
            .context("failed to get article selection")?;
        accumulate(&mut total_usage, &selection_resp.usage);
        self.conversation.add_assistant(&selection_resp.content);
        exchanges.push(Exchange {
            step: "selection".into(),
            prompt: presentation.clone(),
            response: selection_resp.content.clone(),
        });

        let titles: Vec<&str> = results.iter().map(|r| r.title.as_str()).collect();
        let selected_idx = selection::parse_selection(&selection_resp.content, &titles);

        // Step 7: inject article content
        let (title, content) = match selected_idx {
            Some(idx) => {
                let t = &results[idx].title;
                let c = self
                    .knowledge
                    .read(t)
                    .map(|a| a.content.clone())
                    .unwrap_or_else(|| format!("[Article '{}' could not be loaded]", t));
                (t.clone(), c)
            }
            None => {
                let t = &results[0].title;
                let c = self
                    .knowledge
                    .read(t)
                    .map(|a| a.content.clone())
                    .unwrap_or_else(|| "[Article could not be loaded]".into());
                (t.clone(), c)
            }
        };

        let article_prompt = prompts::present_article(&title, &content);
        self.conversation.add_user(&article_prompt);

        // Step 8: get reflection
        let reflection = self
            .inference
            .complete(
                self.conversation.messages(),
                &no_tools,
                &self.config.generation,
            )
            .await
            .context("failed to get reflection")?;
        accumulate(&mut total_usage, &reflection.usage);
        self.conversation.add_assistant(&reflection.content);
        exchanges.push(Exchange {
            step: "reflection".into(),
            prompt: article_prompt.clone(),
            response: reflection.content.clone(),
        });

        // Step 9: log trace
        self.trace_logger.log(&ThinkingTrace {
            timestamp: chrono::Utc::now(),
            specimen_id: self.specimen.id.clone(),
            cycle_number: self.cycle_number,
            exchanges,
            query: query.clone(),
            articles_found,
            article_selected: Some(title.clone()),
            reflection: reflection.content.clone(),
            prompt_tokens: total_usage.prompt_tokens,
            completion_tokens: total_usage.completion_tokens,
        })?;

        Ok(CycleOutcome::Completed {
            query,
            article_selected: Some(title),
            reflection: reflection.content,
        })
    }
}

fn accumulate(total: &mut Usage, add: &Option<Usage>) {
    if let Some(u) = add {
        if let Some(p) = u.prompt_tokens {
            *total.prompt_tokens.get_or_insert(0) += p;
        }
        if let Some(c) = u.completion_tokens {
            *total.completion_tokens.get_or_insert(0) += c;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use aquarium_core::inference::{Completion, FinishReason, Message};
    use aquarium_core::tool::Tool;
    use aquarium_core::specimen::{InferenceBackend, Language};
    use knowledge::article::Article;
    use std::future::Future;
    use std::pin::Pin;
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::Arc;

    /// Mock inference provider returning canned responses in sequence.
    struct MockInference {
        responses: Vec<String>,
        call_count: Arc<AtomicUsize>,
    }

    impl MockInference {
        fn new(responses: Vec<&str>) -> Self {
            Self {
                responses: responses.into_iter().map(String::from).collect(),
                call_count: Arc::new(AtomicUsize::new(0)),
            }
        }
    }

    impl InferenceProvider for MockInference {
        fn complete(
            &self,
            _messages: &[Message],
            _tools: &[Tool],
            _config: &GenerationConfig,
        ) -> Pin<Box<dyn Future<Output = anyhow::Result<Completion>> + Send + '_>> {
            let idx = self.call_count.fetch_add(1, Ordering::SeqCst);
            let content = self
                .responses
                .get(idx)
                .cloned()
                .unwrap_or_else(|| "I have nothing more to say.".into());
            Box::pin(async move {
                Ok(Completion {
                    content,
                    tool_calls: vec![],
                    usage: Some(Usage {
                        prompt_tokens: Some(100),
                        completion_tokens: Some(50),
                    }),
                    finish_reason: FinishReason::Stop,
                })
            })
        }

        fn name(&self) -> &str {
            "mock"
        }

        fn supports_native_tools(&self) -> bool {
            false
        }
    }

    fn test_knowledge_base() -> KnowledgeBase {
        KnowledgeBase::from_articles(vec![
            Article {
                title: "Music and mathematics".into(),
                content: "The basis of musical sound can be described mathematically.".into(),
                categories: vec![],
            },
            Article {
                title: "Pythagorean tuning".into(),
                content: "Pythagorean tuning is a system of musical tuning based on 3:2 ratios."
                    .into(),
                categories: vec![],
            },
            Article {
                title: "Photosynthesis".into(),
                content: "Photosynthesis converts light energy into chemical energy in plants."
                    .into(),
                categories: vec![],
            },
        ])
        .unwrap()
    }

    fn test_specimen() -> SpecimenConfig {
        SpecimenConfig {
            id: "test-adam".into(),
            name: "Adam".into(),
            language: Language::English,
            gender: None,
            has_vision: false,
            system_prompt: "I am Adam. I explore because I am drawn to understanding.".into(),
            inference: InferenceBackend::LocalHttp {
                base_url: "http://localhost:11434".into(),
                model: "mock".into(),
            },
        }
    }

    #[tokio::test]
    async fn full_cycle_produces_trace() {
        let dir = tempfile::TempDir::new().unwrap();

        let mock = MockInference::new(vec![
            "I'm curious about music and mathematics",
            "I'd like to read the first one",
            "The relationship between mathematical ratios and harmony is fascinating.",
        ]);

        let config = LoopConfig {
            max_cycles: Some(1),
            top_k: 3,
            max_conversation_messages: 50,
            trace_dir: dir.path().to_path_buf(),
            generation: GenerationConfig::default(),
        };

        let mut loop_runner = SpecimenLoop::new(
            config,
            test_specimen(),
            test_knowledge_base(),
            Box::new(mock),
        )
        .unwrap();

        loop_runner.run().await.unwrap();

        let trace_path = dir.path().join("test-adam.jsonl");
        assert!(trace_path.exists());

        let contents = std::fs::read_to_string(&trace_path).unwrap();
        let trace: ThinkingTrace = serde_json::from_str(contents.trim()).unwrap();
        assert_eq!(trace.specimen_id, "test-adam");
        assert_eq!(trace.cycle_number, 0);
        assert!(!trace.articles_found.is_empty());
        assert!(trace.article_selected.is_some());
        assert!(trace.reflection.contains("harmony"));

        // Verify exchanges capture the full back-and-forth
        assert_eq!(trace.exchanges.len(), 3);
        assert_eq!(trace.exchanges[0].step, "exploration");
        assert!(!trace.exchanges[0].prompt.is_empty());
        assert!(trace.exchanges[0].response.contains("music"));
        assert_eq!(trace.exchanges[1].step, "selection");
        assert_eq!(trace.exchanges[2].step, "reflection");
        assert!(trace.exchanges[2].response.contains("harmony"));
    }
}
