/// Parse a specimen's choice from a numbered list of articles.
///
/// Handles numeric ("2"), ordinal ("the second one"), and fuzzy title matching.
/// Falls back to the first article if parsing fails — the loop keeps moving.
pub fn parse_selection(response: &str, article_titles: &[&str]) -> Option<usize> {
    if article_titles.is_empty() {
        return None;
    }

    let lower = response.to_lowercase();

    // 1. Try numeric
    if let Some(num) = extract_number(&lower) {
        if num >= 1 && num <= article_titles.len() {
            return Some(num - 1);
        }
    }

    // 2. Try ordinals
    let ordinals: &[(&str, usize)] = &[
        ("first", 0),
        ("second", 1),
        ("third", 2),
        ("fourth", 3),
        ("fifth", 4),
        ("1st", 0),
        ("2nd", 1),
        ("3rd", 2),
        ("4th", 3),
        ("5th", 4),
    ];
    for &(word, idx) in ordinals {
        if lower.contains(word) && idx < article_titles.len() {
            return Some(idx);
        }
    }

    // 3. Fuzzy title match: count significant words from each title in the response
    let mut best: Option<(usize, usize)> = None;
    for (idx, title) in article_titles.iter().enumerate() {
        let title_lower = title.to_lowercase();
        let match_count = title_lower
            .split_whitespace()
            .filter(|w| w.len() > 3)
            .filter(|w| lower.contains(w))
            .count();
        if match_count > 0 && best.map_or(true, |(_, best_count)| match_count > best_count) {
            best = Some((idx, match_count));
        }
    }
    if let Some((idx, _)) = best {
        return Some(idx);
    }

    // 4. Fallback: first article (keep the loop moving)
    tracing::warn!("could not parse selection, defaulting to first: {response:?}");
    Some(0)
}

/// Extract a standalone number from text (not embedded in "3:2" or "1948").
///
/// Only matches digit sequences preceded by whitespace/start and followed by
/// whitespace/end/punctuation (but NOT ':' or other digit-adjacent chars).
fn extract_number(s: &str) -> Option<usize> {
    let chars: Vec<char> = s.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        if chars[i].is_ascii_digit() {
            let start = i;
            while i < chars.len() && chars[i].is_ascii_digit() {
                i += 1;
            }
            // Check boundaries: preceded by whitespace/start, followed by whitespace/end/sentence punct
            let before_ok = start == 0 || chars[start - 1].is_whitespace();
            let after_ok = i >= chars.len()
                || chars[i].is_whitespace()
                || matches!(chars[i], '.' | ',' | '!' | '?' | ')' | ']');
            if before_ok && after_ok {
                let num_str: String = chars[start..i].iter().collect();
                return num_str.parse().ok();
            }
        } else {
            i += 1;
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    const TITLES: &[&str] = &[
        "Music and mathematics",
        "Pythagorean tuning",
        "Fibonacci number",
    ];

    #[test]
    fn numeric_selection() {
        assert_eq!(parse_selection("2", TITLES), Some(1));
        assert_eq!(parse_selection("I'll go with 1", TITLES), Some(0));
        assert_eq!(parse_selection("Number 3 please", TITLES), Some(2));
    }

    #[test]
    fn ordinal_selection() {
        assert_eq!(parse_selection("the second one", TITLES), Some(1));
        assert_eq!(parse_selection("I'd like the third option", TITLES), Some(2));
    }

    #[test]
    fn fuzzy_title_match() {
        assert_eq!(
            parse_selection(
                "The Pythagorean tuning article sounds fascinating",
                TITLES
            ),
            Some(1)
        );
        assert_eq!(
            parse_selection("I'm interested in Fibonacci", TITLES),
            Some(2)
        );
    }

    #[test]
    fn fallback_to_first() {
        assert_eq!(
            parse_selection("hmm, I'm not sure, any of them", TITLES),
            Some(0)
        );
    }

    #[test]
    fn empty_titles() {
        assert_eq!(parse_selection("pick 1", &[]), None);
    }

    #[test]
    fn embedded_number_not_extracted() {
        // "3:2 ratio" should NOT extract 3 — it's part of a ratio, not a selection.
        assert_eq!(
            parse_selection("The 3:2 ratio in Pythagorean tuning is interesting", TITLES),
            Some(1) // Should match via fuzzy title "Pythagorean tuning", not number 3
        );
    }

    #[test]
    fn standalone_number_still_works() {
        assert_eq!(parse_selection("I choose 2", TITLES), Some(1));
        assert_eq!(parse_selection("2.", TITLES), Some(1));
    }

    #[test]
    fn out_of_range_number_falls_through() {
        // Number 5 is out of range for 3 titles, should fall through to other strategies
        assert_eq!(parse_selection("5", TITLES), Some(0)); // fallback
    }
}
