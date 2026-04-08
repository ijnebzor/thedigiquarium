//! Semantic search via Tessera dense embeddings.
//!
//! Only compiled when the `semantic` feature is enabled.

use anyhow::{Context, Result};
use std::path::Path;
use tessera::TesseraDense;

const MAGIC: [u8; 4] = *b"DQEM";
const VERSION: u32 = 1;

/// Pre-computed embedding index for semantic search.
pub struct SemanticIndex {
    embedder: TesseraDense,
    /// Flat f32 buffer: [count * dim] embeddings packed contiguously.
    embeddings: Vec<f32>,
    dim: usize,
    count: usize,
}

#[derive(Debug, Clone)]
pub struct SemanticSearchHit {
    pub article_index: usize,
    pub score: f32,
}

impl SemanticIndex {
    /// Embed all articles and build an in-memory index. Expensive — use `save()`/`load()`.
    pub fn build(articles: &[crate::article::Article], model_id: &str) -> Result<Self> {
        let embedder = TesseraDense::builder()
            .model(model_id)
            .batch_size(1)  // Single-item batches to minimize Metal GPU buffer pressure.
            .yield_ms(2)
            .build()
            .context("failed to init Tessera dense embedder")?;
        let dim = embedder.dimension();

        tracing::info!(
            "embedding {} articles with {} (dim={})",
            articles.len(),
            model_id,
            dim
        );

        let mut all_embeddings = Vec::with_capacity(articles.len() * dim);
        let batch_size = 32;

        for (batch_idx, chunk) in articles.chunks(batch_size).enumerate() {
            let texts: Vec<&str> = chunk.iter().map(|a| a.content.as_str()).collect();
            let batch = embedder
                .encode_batch(&texts)
                .with_context(|| format!("failed to embed batch {}", batch_idx))?;

            for emb in batch {
                all_embeddings.extend(emb.embedding.to_vec());
            }

            if (batch_idx + 1) % 10 == 0 {
                tracing::info!(
                    "embedded {}/{} articles",
                    ((batch_idx + 1) * batch_size).min(articles.len()),
                    articles.len()
                );
            }
        }

        Ok(Self {
            embedder,
            embeddings: all_embeddings,
            dim,
            count: articles.len(),
        })
    }

    /// Serialize embeddings to a binary file.
    pub fn save(&self, path: &Path) -> Result<()> {
        use std::io::Write;
        let mut file = std::fs::File::create(path)
            .with_context(|| format!("failed to create {}", path.display()))?;

        file.write_all(&MAGIC)?;
        file.write_all(&VERSION.to_le_bytes())?;
        file.write_all(&(self.dim as u32).to_le_bytes())?;
        file.write_all(&(self.count as u32).to_le_bytes())?;

        // Safe: f32 is Pod (plain old data), no padding concerns.
        let byte_len = self.embeddings.len() * size_of::<f32>();
        let bytes: &[u8] =
            unsafe { std::slice::from_raw_parts(self.embeddings.as_ptr() as *const u8, byte_len) };
        file.write_all(bytes)?;

        tracing::info!(
            "saved semantic index: {} articles, {} dims, {:.1} MB",
            self.count,
            self.dim,
            byte_len as f64 / 1_048_576.0
        );
        Ok(())
    }

    /// Load pre-computed embeddings from disk. Also initialises the embedder for queries.
    pub fn load(path: &Path, model_id: &str) -> Result<Self> {
        use std::io::Read;
        let mut file = std::fs::File::open(path)
            .with_context(|| format!("failed to open {}", path.display()))?;

        let mut magic = [0u8; 4];
        file.read_exact(&mut magic)?;
        anyhow::ensure!(magic == MAGIC, "invalid index file magic");

        let mut buf4 = [0u8; 4];
        file.read_exact(&mut buf4)?;
        let version = u32::from_le_bytes(buf4);
        anyhow::ensure!(version == VERSION, "unsupported index version: {version}");

        file.read_exact(&mut buf4)?;
        let dim = u32::from_le_bytes(buf4) as usize;

        file.read_exact(&mut buf4)?;
        let count = u32::from_le_bytes(buf4) as usize;

        let n_floats = count * dim;
        let mut bytes = vec![0u8; n_floats * size_of::<f32>()];
        file.read_exact(&mut bytes)?;

        let embeddings: Vec<f32> = unsafe {
            let ptr = bytes.as_ptr() as *const f32;
            std::slice::from_raw_parts(ptr, n_floats).to_vec()
        };

        let embedder = TesseraDense::builder()
            .model(model_id)
            .batch_size(1)
            .yield_ms(2)
            .build()
            .context("failed to init Tessera embedder for queries")?;
        anyhow::ensure!(
            embedder.dimension() == dim,
            "model dim ({}) != index dim ({dim})",
            embedder.dimension()
        );

        tracing::info!("loaded semantic index: {} articles, {} dims", count, dim);

        Ok(Self {
            embedder,
            embeddings,
            dim,
            count,
        })
    }

    /// Search by cosine similarity against the query.
    pub fn search(&self, query: &str, top_k: usize) -> Result<Vec<SemanticSearchHit>> {
        let query_emb = self.embedder.encode(query).context("failed to embed query")?;
        let q = query_emb.embedding.to_vec();

        let mut hits: Vec<SemanticSearchHit> = (0..self.count)
            .map(|idx| {
                let doc = &self.embeddings[idx * self.dim..(idx + 1) * self.dim];
                SemanticSearchHit {
                    article_index: idx,
                    score: cosine_similarity(&q, doc),
                }
            })
            .collect();

        hits.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        hits.truncate(top_k);
        Ok(hits)
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    debug_assert_eq!(a.len(), b.len());
    let dot: f32 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }
    dot / (norm_a * norm_b)
}
