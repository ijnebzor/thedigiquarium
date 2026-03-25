use crate::article::Article;
use crate::tokenizer;
use std::collections::HashMap;

const K1: f32 = 1.2;
const B: f32 = 0.75;

/// BM25 inverted index over a corpus of articles.
pub struct TextIndex {
    /// term -> vec of (article_index, term_frequency)
    postings: HashMap<String, Vec<(usize, u32)>>,
    doc_count: usize,
    doc_lengths: Vec<u32>,
    avg_doc_length: f32,
    /// title_lowercase -> article_index
    title_index: HashMap<String, usize>,
}

#[derive(Debug, Clone)]
pub struct TextSearchHit {
    pub article_index: usize,
    pub score: f32,
}

impl TextIndex {
    /// Build the index from a corpus. Title tokens receive 3x weight.
    pub fn build(articles: &[Article]) -> Self {
        let doc_count = articles.len();
        let mut postings: HashMap<String, Vec<(usize, u32)>> = HashMap::new();
        let mut doc_lengths = Vec::with_capacity(doc_count);
        let mut title_index = HashMap::new();

        for (idx, article) in articles.iter().enumerate() {
            title_index.insert(article.title.to_lowercase(), idx);

            let title_tokens = tokenizer::tokenize(&article.title);
            let content_tokens = tokenizer::tokenize(&article.content);

            let mut term_freqs: HashMap<String, u32> = HashMap::new();
            for token in &title_tokens {
                if !tokenizer::is_stop_word(token) {
                    *term_freqs.entry(token.clone()).or_default() += 3;
                }
            }
            for token in &content_tokens {
                if !tokenizer::is_stop_word(token) {
                    *term_freqs.entry(token.clone()).or_default() += 1;
                }
            }

            let doc_length = (title_tokens.len() * 3 + content_tokens.len()) as u32;
            doc_lengths.push(doc_length);

            for (term, freq) in term_freqs {
                postings.entry(term).or_default().push((idx, freq));
            }
        }

        let avg_doc_length = if doc_count > 0 {
            doc_lengths.iter().map(|&l| l as f64).sum::<f64>() / doc_count as f64
        } else {
            1.0
        } as f32;

        tracing::info!(
            "built text index: {} docs, {} terms, avg_len={:.1}",
            doc_count,
            postings.len(),
            avg_doc_length
        );

        Self {
            postings,
            doc_count,
            doc_lengths,
            avg_doc_length,
            title_index,
        }
    }

    /// Search with BM25 scoring. Returns hits sorted by relevance.
    pub fn search(&self, query: &str, top_k: usize) -> Vec<TextSearchHit> {
        let query_tokens = tokenizer::tokenize(query);
        let mut scores: HashMap<usize, f32> = HashMap::new();

        for token in &query_tokens {
            if tokenizer::is_stop_word(token) {
                continue;
            }
            if let Some(posting_list) = self.postings.get(token) {
                let df = posting_list.len() as f32;
                let n = self.doc_count as f32;
                let idf = ((n - df + 0.5) / (df + 0.5) + 1.0).ln();

                for &(doc_idx, tf) in posting_list {
                    let tf = tf as f32;
                    let dl = self.doc_lengths[doc_idx] as f32;
                    let tf_norm =
                        (tf * (K1 + 1.0)) / (tf + K1 * (1.0 - B + B * dl / self.avg_doc_length));
                    *scores.entry(doc_idx).or_default() += idf * tf_norm;
                }
            }
        }

        let mut hits: Vec<TextSearchHit> = scores
            .into_iter()
            .map(|(article_index, score)| TextSearchHit {
                article_index,
                score,
            })
            .collect();

        hits.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        hits.truncate(top_k);
        hits
    }

    /// Exact title lookup (case-insensitive).
    pub fn find_by_title(&self, title: &str) -> Option<usize> {
        self.title_index.get(&title.to_lowercase()).copied()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_corpus() -> Vec<Article> {
        vec![
            Article {
                title: "Pythagorean tuning".into(),
                content: "Pythagorean tuning is a system of musical tuning in which the frequency ratios of all intervals are based on the ratio 3:2. This ratio is chosen because it is the next harmonic of a vibrating string.".into(),
                categories: vec![],
            },
            Article {
                title: "Music and mathematics".into(),
                content: "Music theory has no axiomatic foundation in modern mathematics, yet the basis of musical sound can be described mathematically. The fundamentals of music theory include intervals, scales, and rhythm.".into(),
                categories: vec![],
            },
            Article {
                title: "Fibonacci number".into(),
                content: "In mathematics, the Fibonacci sequence is a sequence in which each number is the sum of the two preceding ones. Numbers that are part of the Fibonacci sequence are known as Fibonacci numbers.".into(),
                categories: vec![],
            },
            Article {
                title: "Photosynthesis".into(),
                content: "Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy that can be stored and later released to fuel the organism's activities.".into(),
                categories: vec![],
            },
        ]
    }

    #[test]
    fn search_finds_relevant_articles() {
        let corpus = sample_corpus();
        let index = TextIndex::build(&corpus);
        let hits = index.search("music mathematics", 3);

        assert!(!hits.is_empty());
        // "Music and mathematics" should rank highly
        let titles: Vec<&str> = hits.iter().map(|h| corpus[h.article_index].title.as_str()).collect();
        assert!(titles.contains(&"Music and mathematics"));
    }

    #[test]
    fn title_match_ranks_high() {
        let corpus = sample_corpus();
        let index = TextIndex::build(&corpus);
        let hits = index.search("pythagorean tuning", 3);

        assert!(!hits.is_empty());
        assert_eq!(corpus[hits[0].article_index].title, "Pythagorean tuning");
    }

    #[test]
    fn unrelated_query_excludes_irrelevant() {
        let corpus = sample_corpus();
        let index = TextIndex::build(&corpus);
        let hits = index.search("photosynthesis plants", 2);

        assert!(!hits.is_empty());
        assert_eq!(corpus[hits[0].article_index].title, "Photosynthesis");
    }

    #[test]
    fn find_by_title_case_insensitive() {
        let corpus = sample_corpus();
        let index = TextIndex::build(&corpus);
        assert_eq!(index.find_by_title("PYTHAGOREAN TUNING"), Some(0));
        assert_eq!(index.find_by_title("pythagorean tuning"), Some(0));
        assert_eq!(index.find_by_title("nonexistent"), None);
    }

    #[test]
    fn empty_corpus() {
        let index = TextIndex::build(&[]);
        let hits = index.search("anything", 5);
        assert!(hits.is_empty());
    }

    #[test]
    fn empty_query() {
        let corpus = sample_corpus();
        let index = TextIndex::build(&corpus);
        let hits = index.search("", 5);
        assert!(hits.is_empty());
    }
}
