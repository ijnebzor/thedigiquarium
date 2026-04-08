/// Tokenize and normalize text for the inverted index.
///
/// Handles Unicode case folding, CJK character segmentation (each ideograph
/// becomes its own token), punctuation removal, and whitespace splitting.
pub fn tokenize(text: &str) -> Vec<String> {
    let lower = text.to_lowercase();
    let mut tokens = Vec::new();
    let mut current = String::new();

    for ch in lower.chars() {
        if is_cjk(ch) {
            if !current.is_empty() {
                tokens.push(std::mem::take(&mut current));
            }
            tokens.push(ch.to_string());
        } else if ch.is_alphanumeric() {
            current.push(ch);
        } else if !current.is_empty() {
            tokens.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }

    tokens
}

fn is_cjk(ch: char) -> bool {
    matches!(ch as u32,
        0x4E00..=0x9FFF   // CJK Unified Ideographs
        | 0x3400..=0x4DBF // Extension A
        | 0x20000..=0x2A6DF // Extension B
        | 0xF900..=0xFAFF // Compatibility Ideographs
        | 0x3040..=0x309F // Hiragana
        | 0x30A0..=0x30FF // Katakana
        | 0xAC00..=0xD7AF // Hangul
    )
}

pub fn is_stop_word(word: &str) -> bool {
    matches!(
        word,
        "a" | "an"
            | "the"
            | "is"
            | "are"
            | "was"
            | "were"
            | "be"
            | "been"
            | "being"
            | "have"
            | "has"
            | "had"
            | "do"
            | "does"
            | "did"
            | "will"
            | "would"
            | "could"
            | "should"
            | "may"
            | "might"
            | "shall"
            | "can"
            | "to"
            | "of"
            | "in"
            | "for"
            | "on"
            | "with"
            | "at"
            | "by"
            | "from"
            | "as"
            | "into"
            | "through"
            | "during"
            | "before"
            | "after"
            | "above"
            | "below"
            | "between"
            | "and"
            | "but"
            | "or"
            | "not"
            | "no"
            | "nor"
            | "so"
            | "if"
            | "then"
            | "than"
            | "that"
            | "this"
            | "these"
            | "those"
            | "it"
            | "its"
            | "he"
            | "she"
            | "they"
            | "them"
            | "his"
            | "her"
            | "their"
            | "we"
            | "our"
            | "you"
            | "your"
            | "i"
            | "me"
            | "my"
            | "which"
            | "who"
            | "whom"
            | "what"
            | "where"
            | "when"
            | "how"
            | "why"
            | "each"
            | "every"
            | "all"
            | "both"
            | "few"
            | "more"
            | "most"
            | "other"
            | "some"
            | "such"
            | "only"
            | "own"
            | "same"
            | "also"
            | "just"
            | "about"
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_tokenization() {
        let tokens = tokenize("Hello, World!");
        assert_eq!(tokens, vec!["hello", "world"]);
    }

    #[test]
    fn cjk_segmentation() {
        let tokens = tokenize("音楽と数学");
        assert_eq!(tokens, vec!["音", "楽", "と", "数", "学"]);
    }

    #[test]
    fn mixed_cjk_and_latin() {
        let tokens = tokenize("hello 世界 world");
        assert_eq!(tokens, vec!["hello", "世", "界", "world"]);
    }

    #[test]
    fn empty_input() {
        assert!(tokenize("").is_empty());
        assert!(tokenize("   ").is_empty());
    }

    #[test]
    fn stop_words() {
        assert!(is_stop_word("the"));
        assert!(is_stop_word("is"));
        assert!(!is_stop_word("music"));
        assert!(!is_stop_word("mathematics"));
    }
}
