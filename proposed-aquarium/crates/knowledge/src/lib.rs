pub mod article;
pub mod rank_fusion;
pub mod text_search;
pub mod tokenizer;

#[cfg(feature = "semantic")]
pub mod semantic;

#[cfg(feature = "semantic")]
use anyhow::Context;
use anyhow::Result;
use article::Article;

/// A search result returned by the knowledge base.
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub title: String,
    pub snippet: String,
    pub score: f32,
}

/// Configuration for building a [`KnowledgeBase`].
pub struct KnowledgeBaseConfig {
    /// Path to articles — JSONL file or directory of .txt/.md files.
    pub corpus_path: std::path::PathBuf,
    /// Path to a pre-built semantic embedding index (only used with `semantic` feature).
    pub semantic_index_path: Option<std::path::PathBuf>,
    /// Tessera model ID for semantic search (default: `bge-base-en-v1.5`).
    pub semantic_model: String,
    /// Snippet length in characters for search results.
    pub snippet_length: usize,
}

impl Default for KnowledgeBaseConfig {
    fn default() -> Self {
        Self {
            corpus_path: std::path::PathBuf::from("corpus.jsonl"),
            semantic_index_path: None,
            semantic_model: "bge-base-en-v1.5".into(),
            snippet_length: 200,
        }
    }
}

/// Wikipedia knowledge base with text search and optional semantic search.
pub struct KnowledgeBase {
    articles: Vec<Article>,
    text_index: text_search::TextIndex,
    #[cfg(feature = "semantic")]
    semantic_index: Option<semantic::SemanticIndex>,
    snippet_length: usize,
}

impl KnowledgeBase {
    /// Open a knowledge base from the given config.
    pub fn open(config: KnowledgeBaseConfig) -> Result<Self> {
        let articles = if config.corpus_path.is_dir() {
            article::load_directory(&config.corpus_path)?
        } else {
            article::load_jsonl(&config.corpus_path)?
        };
        anyhow::ensure!(!articles.is_empty(), "corpus is empty");

        let text_index = text_search::TextIndex::build(&articles);

        #[cfg(feature = "semantic")]
        let semantic_index = if let Some(ref idx_path) = config.semantic_index_path {
            if idx_path.exists() {
                Some(
                    semantic::SemanticIndex::load(idx_path, &config.semantic_model)
                        .context("failed to load semantic index")?,
                )
            } else {
                tracing::warn!(
                    "semantic index not found: {} — text-only search",
                    idx_path.display()
                );
                None
            }
        } else {
            None
        };

        tracing::info!(
            "knowledge base ready: {} articles, text=true, semantic={}",
            articles.len(),
            cfg!(feature = "semantic"),
        );

        Ok(Self {
            articles,
            text_index,
            #[cfg(feature = "semantic")]
            semantic_index,
            snippet_length: config.snippet_length,
        })
    }

    /// Build from articles directly (useful for testing).
    pub fn from_articles(articles: Vec<Article>) -> Result<Self> {
        anyhow::ensure!(!articles.is_empty(), "corpus is empty");
        let text_index = text_search::TextIndex::build(&articles);
        Ok(Self {
            articles,
            text_index,
            #[cfg(feature = "semantic")]
            semantic_index: None,
            snippet_length: 200,
        })
    }

    /// Search for articles matching a query. Uses text search always, semantic if
    /// available, and RRF to combine results.
    pub fn search(&self, query: &str, top_k: usize) -> Result<Vec<SearchResult>> {
        let text_hits = self.text_index.search(query, top_k * 2);
        let text_rankings: Vec<usize> = text_hits.iter().map(|h| h.article_index).collect();

        #[allow(unused_mut)]
        let mut ranked_lists = vec![text_rankings];

        #[cfg(feature = "semantic")]
        if let Some(ref sem) = self.semantic_index {
            match sem.search(query, top_k * 2) {
                Ok(sem_hits) => {
                    ranked_lists.push(sem_hits.iter().map(|h| h.article_index).collect());
                }
                Err(e) => {
                    tracing::warn!("semantic search failed, text-only: {e}");
                }
            }
        }

        if ranked_lists.len() == 1 {
            // No fusion needed — return text results directly.
            return Ok(text_hits
                .iter()
                .take(top_k)
                .map(|h| self.hit_to_result(h.article_index, h.score))
                .collect());
        }

        let fused = rank_fusion::reciprocal_rank_fusion(&ranked_lists, top_k);
        Ok(fused
            .iter()
            .map(|f| self.hit_to_result(f.article_index, f.rrf_score))
            .collect())
    }

    /// Read an article by exact title (case-insensitive).
    pub fn read(&self, title: &str) -> Option<&Article> {
        self.text_index
            .find_by_title(title)
            .map(|idx| &self.articles[idx])
    }

    /// Return a random article.
    pub fn random(&self) -> &Article {
        use rand::Rng;
        let idx = rand::rng().random_range(0..self.articles.len());
        &self.articles[idx]
    }

    /// Total number of articles in the corpus.
    pub fn article_count(&self) -> usize {
        self.articles.len()
    }

    fn hit_to_result(&self, idx: usize, score: f32) -> SearchResult {
        let a = &self.articles[idx];
        SearchResult {
            title: a.title.clone(),
            snippet: a.snippet(self.snippet_length).to_string(),
            score,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_corpus() -> Vec<Article> {
        vec![
            Article {
                title: "Pythagorean tuning".into(),
                content: "Pythagorean tuning is a system of musical tuning in which the frequency ratios of all intervals are based on the ratio 3:2.".into(),
                categories: vec![],
            },
            Article {
                title: "Music and mathematics".into(),
                content: "The basis of musical sound can be described mathematically using frequency ratios and harmonic series.".into(),
                categories: vec![],
            },
            Article {
                title: "Photosynthesis".into(),
                content: "Photosynthesis is a process used by plants to convert light energy into chemical energy.".into(),
                categories: vec![],
            },
        ]
    }

    #[test]
    fn search_returns_results() {
        let kb = KnowledgeBase::from_articles(test_corpus()).unwrap();
        let results = kb.search("music mathematics", 3).unwrap();
        assert!(!results.is_empty());
        assert!(results.iter().any(|r| r.title == "Music and mathematics"));
    }

    #[test]
    fn read_by_title() {
        let kb = KnowledgeBase::from_articles(test_corpus()).unwrap();
        let article = kb.read("Pythagorean tuning").unwrap();
        assert!(article.content.contains("frequency ratios"));
        assert!(kb.read("nonexistent").is_none());
    }

    #[test]
    fn random_returns_article() {
        let kb = KnowledgeBase::from_articles(test_corpus()).unwrap();
        let article = kb.random();
        assert!(!article.title.is_empty());
    }

    #[test]
    fn article_count() {
        let kb = KnowledgeBase::from_articles(test_corpus()).unwrap();
        assert_eq!(kb.article_count(), 3);
    }
}
