/// Extract a search query from a specimen's natural language response.
///
/// Strategy:
/// 1. Short responses (<=15 words): use the whole thing.
/// 2. Look for signal phrases ("I'd like to learn about...", "curious about...", etc.)
/// 3. Fallback: first sentence, capped at 10 words.
pub fn extract_search_query(response: &str) -> String {
    let trimmed = response.trim();
    if trimmed.is_empty() {
        return String::new();
    }

    let word_count = trimmed.split_whitespace().count();
    if word_count <= 15 {
        return trimmed
            .trim_end_matches(|c: char| c == '.' || c == '!' || c == '?')
            .to_string();
    }

    let lower = trimmed.to_lowercase();
    let signal_phrases = [
        "i'd like to learn about",
        "i would like to learn about",
        "i'd like to explore",
        "i would like to explore",
        "i'm curious about",
        "i am curious about",
        "i want to know about",
        "i want to explore",
        "i want to learn about",
        "i'm interested in",
        "i am interested in",
        "curious about",
        "want to understand",
        "want to know more about",
        "like to read about",
        "fascinated by",
        "intrigued by",
    ];

    for phrase in &signal_phrases {
        if let Some(pos) = lower.find(phrase) {
            let start = pos + phrase.len();
            // Slice from `lower` (not `trimmed`) to avoid byte-offset mismatch
            // when to_lowercase() changes string length (e.g. 'ẞ' → "ss").
            let remainder = &lower[start..];
            let query = remainder
                .split(|c: char| c == '.' || c == '!' || c == '?' || c == '\n')
                .next()
                .unwrap_or(remainder)
                .trim();
            if !query.is_empty() {
                return query.to_string();
            }
        }
    }

    // Fallback: first sentence, capped at 10 words
    let first_sentence = trimmed
        .split(|c: char| c == '.' || c == '!' || c == '?')
        .next()
        .unwrap_or(trimmed)
        .trim();

    let words: Vec<&str> = first_sentence.split_whitespace().collect();
    if words.len() > 10 {
        words[..10].join(" ")
    } else {
        first_sentence.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn short_response_used_directly() {
        assert_eq!(
            extract_search_query("music and mathematics"),
            "music and mathematics"
        );
    }

    #[test]
    fn strips_trailing_punctuation() {
        assert_eq!(
            extract_search_query("Pythagorean tuning."),
            "Pythagorean tuning"
        );
    }

    #[test]
    fn signal_phrase_extraction() {
        let response = "After thinking about it, I'm curious about how plants communicate with each other through underground networks.";
        let query = extract_search_query(response);
        assert_eq!(
            query,
            "how plants communicate with each other through underground networks"
        );
    }

    #[test]
    fn long_response_uses_first_sentence() {
        let response = "I have been contemplating the nature of consciousness and awareness. There are many philosophical traditions that address this topic. Buddhist philosophy in particular has interesting perspectives on the nature of mind.";
        let query = extract_search_query(response);
        // First sentence, capped at 10 words
        assert_eq!(
            query,
            "I have been contemplating the nature of consciousness and awareness"
        );
    }

    #[test]
    fn empty_response() {
        assert_eq!(extract_search_query(""), "");
        assert_eq!(extract_search_query("   "), "");
    }

    #[test]
    fn unicode_lowercasing_does_not_panic() {
        // German capital sharp S lowercases to "ss" (different byte length).
        let response = "Ich bin \u{1E9E}ehr curious about quantum mechanics and wave functions in this fascinating topic.";
        // Should not panic — just extract what it can.
        let query = extract_search_query(response);
        assert!(!query.is_empty());
    }

    #[test]
    fn id_like_to_explore() {
        let response = "I've been thinking a lot lately, and I'd like to explore the relationship between music and emotion in different cultures.";
        let query = extract_search_query(response);
        assert_eq!(
            query,
            "the relationship between music and emotion in different cultures"
        );
    }
}
