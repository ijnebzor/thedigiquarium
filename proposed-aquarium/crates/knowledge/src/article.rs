use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

/// A single Wikipedia article.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Article {
    /// Canonical article title (e.g. "Pythagorean tuning").
    pub title: String,
    /// Full plain-text content.
    pub content: String,
    /// Optional categories or tags.
    #[serde(default)]
    pub categories: Vec<String>,
}

impl Article {
    pub fn word_count(&self) -> usize {
        self.content.split_whitespace().count()
    }

    /// First `max_chars` characters as a snippet for search results.
    pub fn snippet(&self, max_chars: usize) -> &str {
        if self.content.len() <= max_chars {
            return &self.content;
        }
        let mut end = max_chars;
        while !self.content.is_char_boundary(end) && end > 0 {
            end -= 1;
        }
        &self.content[..end]
    }
}

/// Load articles from a JSONL file (one JSON object per line).
pub fn load_jsonl(path: &Path) -> Result<Vec<Article>> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;

    let mut articles = Vec::new();
    for (i, line) in content.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let article: Article = serde_json::from_str(line)
            .with_context(|| format!("failed to parse article at line {}", i + 1))?;
        articles.push(article);
    }

    tracing::info!("loaded {} articles from {}", articles.len(), path.display());
    Ok(articles)
}

/// Load articles from a directory of plain-text files.
///
/// Filename (without extension) becomes the title; underscores become spaces.
pub fn load_directory(dir: &Path) -> Result<Vec<Article>> {
    anyhow::ensure!(dir.is_dir(), "not a directory: {}", dir.display());

    let mut entries: Vec<_> = std::fs::read_dir(dir)
        .with_context(|| format!("failed to read {}", dir.display()))?
        .collect::<std::result::Result<Vec<_>, _>>()?;
    entries.sort_by_key(|e| e.file_name());

    let mut articles = Vec::new();
    for entry in entries {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
        if ext != "txt" && ext != "md" {
            continue;
        }

        let title = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("Untitled")
            .replace('_', " ");

        let content = std::fs::read_to_string(&path)
            .with_context(|| format!("failed to read {}", path.display()))?;

        articles.push(Article {
            title,
            content,
            categories: Vec::new(),
        });
    }

    tracing::info!("loaded {} articles from {}", articles.len(), dir.display());
    Ok(articles)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::TempDir;

    fn temp_dir_with_articles() -> TempDir {
        let dir = TempDir::new().unwrap();
        std::fs::write(
            dir.path().join("Pythagorean_tuning.txt"),
            "Pythagorean tuning is a system of musical tuning...",
        )
        .unwrap();
        std::fs::write(
            dir.path().join("Music_and_mathematics.txt"),
            "Music and mathematics have a deep historical relationship...",
        )
        .unwrap();
        dir
    }

    fn temp_jsonl() -> tempfile::NamedTempFile {
        let mut f = tempfile::NamedTempFile::new().unwrap();
        writeln!(
            f,
            r#"{{"title":"Alpha","content":"Alpha content here","categories":["Science"]}}"#
        )
        .unwrap();
        writeln!(
            f,
            r#"{{"title":"Beta","content":"Beta content here","categories":[]}}"#
        )
        .unwrap();
        f
    }

    #[test]
    fn load_directory_reads_txt_files() {
        let dir = temp_dir_with_articles();
        let articles = load_directory(dir.path()).unwrap();
        assert_eq!(articles.len(), 2);
        assert!(articles.iter().any(|a| a.title == "Music and mathematics"));
        assert!(articles.iter().any(|a| a.title == "Pythagorean tuning"));
    }

    #[test]
    fn load_jsonl_parses_lines() {
        let f = temp_jsonl();
        let articles = load_jsonl(f.path()).unwrap();
        assert_eq!(articles.len(), 2);
        assert_eq!(articles[0].title, "Alpha");
        assert_eq!(articles[1].title, "Beta");
        assert_eq!(articles[0].categories, vec!["Science"]);
    }

    #[test]
    fn snippet_respects_char_boundary() {
        let article = Article {
            title: "Test".into(),
            content: "cafe\u{0301} au lait".into(), // café with combining accent
            categories: vec![],
        };
        let s = article.snippet(5);
        assert!(s.len() <= 5);
        // Should not panic on char boundary
    }
}
