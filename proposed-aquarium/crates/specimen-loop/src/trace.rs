use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::io::Write;
use std::path::Path;

/// A single prompt→response exchange within a cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Exchange {
    /// Which step of the manufactured loop this belongs to.
    pub step: String,
    /// The prompt sent to the specimen (user message).
    pub prompt: String,
    /// The specimen's raw response (assistant message).
    pub response: String,
}

/// A single thinking trace entry — one exploration cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThinkingTrace {
    pub timestamp: DateTime<Utc>,
    pub specimen_id: String,
    pub cycle_number: u64,
    /// The full back-and-forth between the manufactured loop and the specimen.
    pub exchanges: Vec<Exchange>,
    pub query: String,
    pub articles_found: Vec<String>,
    pub article_selected: Option<String>,
    pub reflection: String,
    pub prompt_tokens: Option<u32>,
    pub completion_tokens: Option<u32>,
}

/// Appends thinking traces to a JSONL file.
pub struct TraceLogger {
    file: std::io::BufWriter<std::fs::File>,
    path: std::path::PathBuf,
}

impl TraceLogger {
    /// Open (or create) a trace log for a specimen.
    pub fn open(dir: &Path, specimen_id: &str) -> Result<Self> {
        std::fs::create_dir_all(dir)
            .with_context(|| format!("failed to create trace dir: {}", dir.display()))?;

        let path = dir.join(format!("{specimen_id}.jsonl"));
        let file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .with_context(|| format!("failed to open trace file: {}", path.display()))?;

        Ok(Self {
            file: std::io::BufWriter::new(file),
            path,
        })
    }

    /// Append a trace entry.
    pub fn log(&mut self, trace: &ThinkingTrace) -> Result<()> {
        let json =
            serde_json::to_string(trace).context("failed to serialize thinking trace")?;
        writeln!(self.file, "{json}")
            .with_context(|| format!("failed to write to {}", self.path.display()))?;
        self.file.flush()?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn trace_roundtrip() {
        let trace = ThinkingTrace {
            timestamp: Utc::now(),
            specimen_id: "adam".into(),
            cycle_number: 42,
            exchanges: vec![
                Exchange {
                    step: "exploration".into(),
                    prompt: "What topic interests you?".into(),
                    response: "I'm curious about music".into(),
                },
                Exchange {
                    step: "reflection".into(),
                    prompt: "Here is the article...".into(),
                    response: "Fascinating connections.".into(),
                },
            ],
            query: "music mathematics".into(),
            articles_found: vec!["Music and mathematics".into()],
            article_selected: Some("Music and mathematics".into()),
            reflection: "Fascinating connections between harmony and ratios.".into(),
            prompt_tokens: Some(150),
            completion_tokens: Some(80),
        };

        let json = serde_json::to_string(&trace).unwrap();
        let parsed: ThinkingTrace = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.specimen_id, "adam");
        assert_eq!(parsed.cycle_number, 42);
        assert_eq!(parsed.exchanges.len(), 2);
        assert_eq!(parsed.exchanges[0].step, "exploration");
        assert_eq!(parsed.exchanges[1].response, "Fascinating connections.");
    }

    #[test]
    fn logger_writes_to_file() {
        let dir = tempfile::TempDir::new().unwrap();
        let mut logger = TraceLogger::open(dir.path(), "test-specimen").unwrap();

        let trace = ThinkingTrace {
            timestamp: Utc::now(),
            specimen_id: "test-specimen".into(),
            cycle_number: 0,
            exchanges: vec![Exchange {
                step: "exploration".into(),
                prompt: "What interests you?".into(),
                response: "test response".into(),
            }],
            query: "test".into(),
            articles_found: vec![],
            article_selected: None,
            reflection: "test reflection".into(),
            prompt_tokens: None,
            completion_tokens: None,
        };

        logger.log(&trace).unwrap();

        let contents =
            std::fs::read_to_string(dir.path().join("test-specimen.jsonl")).unwrap();
        assert!(contents.contains("test reflection"));
        assert!(contents.contains("What interests you?"));
    }
}
