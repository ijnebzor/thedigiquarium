use std::collections::HashMap;

/// Standard RRF constant (Cormack et al.).
const K: f32 = 60.0;

#[derive(Debug, Clone)]
pub struct FusedResult {
    pub article_index: usize,
    pub rrf_score: f32,
}

/// Reciprocal Rank Fusion: combine multiple ranked lists by rank position.
///
/// Each input list is article indices in relevance order. Original scores are
/// ignored — only rank matters.
pub fn reciprocal_rank_fusion(ranked_lists: &[Vec<usize>], top_k: usize) -> Vec<FusedResult> {
    let mut scores: HashMap<usize, f32> = HashMap::new();

    for list in ranked_lists {
        for (rank, &article_index) in list.iter().enumerate() {
            *scores.entry(article_index).or_default() += 1.0 / (K + rank as f32 + 1.0);
        }
    }

    let mut fused: Vec<FusedResult> = scores
        .into_iter()
        .map(|(article_index, rrf_score)| FusedResult {
            article_index,
            rrf_score,
        })
        .collect();

    fused.sort_by(|a, b| b.rrf_score.partial_cmp(&a.rrf_score).unwrap_or(std::cmp::Ordering::Equal));
    fused.truncate(top_k);
    fused
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn single_list_preserves_order() {
        let lists = vec![vec![3, 1, 4, 0, 5]];
        let fused = reciprocal_rank_fusion(&lists, 3);
        assert_eq!(fused.len(), 3);
        // Rank 0 item (index 3) should have highest RRF score
        assert_eq!(fused[0].article_index, 3);
        assert_eq!(fused[1].article_index, 1);
        assert_eq!(fused[2].article_index, 4);
    }

    #[test]
    fn overlapping_lists_boost_shared_items() {
        // Article 2 appears in both lists, should rank highest
        let lists = vec![vec![0, 2, 3], vec![1, 2, 4]];
        let fused = reciprocal_rank_fusion(&lists, 5);
        assert_eq!(fused[0].article_index, 2);
    }

    #[test]
    fn empty_lists() {
        let fused = reciprocal_rank_fusion(&[], 5);
        assert!(fused.is_empty());
    }
}
