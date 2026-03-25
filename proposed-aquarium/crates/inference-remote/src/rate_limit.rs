use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};

use crate::provider::Provider;

/// Tracks rate limit state across providers using response headers.
pub struct RateLimitTracker {
    state: Mutex<HashMap<Provider, RateLimitState>>,
}

/// Rate limit state for a single provider.
#[derive(Debug, Clone)]
struct RateLimitState {
    remaining_requests: Option<u32>,
    remaining_tokens: Option<u32>,
    /// When the rate limit resets (as a monotonic instant).
    reset_at: Option<Instant>,
}

impl RateLimitTracker {
    pub fn new() -> Self {
        Self {
            state: Mutex::new(HashMap::new()),
        }
    }

    /// Check whether a provider is likely available (not rate-limited).
    pub fn is_available(&self, provider: &Provider) -> bool {
        let state = self.state.lock().unwrap();
        match state.get(provider) {
            None => true,
            Some(s) => {
                // If we have a reset time and it's in the future, we're limited.
                if let Some(reset_at) = s.reset_at {
                    if Instant::now() < reset_at {
                        return false;
                    }
                }
                // If remaining requests is explicitly zero, we're limited.
                if s.remaining_requests == Some(0) {
                    // Check if reset time has passed.
                    return s.reset_at.is_some_and(|r| Instant::now() >= r);
                }
                true
            }
        }
    }

    /// Update rate limit state from HTTP response headers.
    ///
    /// Parses the common OpenAI-compatible rate limit headers:
    /// - `x-ratelimit-remaining-requests`
    /// - `x-ratelimit-remaining-tokens`
    /// - `x-ratelimit-reset-requests` (seconds or duration string)
    /// - `x-ratelimit-reset-tokens`
    /// - `retry-after` (seconds)
    pub fn update_from_headers(
        &self,
        provider: &Provider,
        headers: &reqwest::header::HeaderMap,
    ) {
        let remaining_requests = parse_header_u32(headers, "x-ratelimit-remaining-requests");
        let remaining_tokens = parse_header_u32(headers, "x-ratelimit-remaining-tokens");

        let reset_secs = parse_header_duration(headers, "x-ratelimit-reset-requests")
            .or_else(|| parse_header_duration(headers, "retry-after"));

        let reset_at = reset_secs.map(|d| Instant::now() + d);

        let mut state = self.state.lock().unwrap();
        let entry = state.entry(*provider).or_insert_with(|| RateLimitState {
            remaining_requests: None,
            remaining_tokens: None,
            reset_at: None,
        });

        if remaining_requests.is_some() {
            entry.remaining_requests = remaining_requests;
        }
        if remaining_tokens.is_some() {
            entry.remaining_tokens = remaining_tokens;
        }
        if reset_at.is_some() {
            entry.reset_at = reset_at;
        }
    }

    /// Mark a provider as rate-limited with a fallback cooldown.
    /// Used when we get a 429 but headers don't include reset timing.
    pub fn mark_rate_limited(&self, provider: &Provider, cooldown: Duration) {
        let mut state = self.state.lock().unwrap();
        let entry = state.entry(*provider).or_insert_with(|| RateLimitState {
            remaining_requests: None,
            remaining_tokens: None,
            reset_at: None,
        });
        entry.remaining_requests = Some(0);
        entry.reset_at = Some(Instant::now() + cooldown);
    }

    /// Clear rate limit state for a provider (e.g. after reset or successful request).
    #[allow(dead_code)]
    pub fn clear(&self, provider: &Provider) {
        self.state.lock().unwrap().remove(provider);
    }
}

fn parse_header_u32(headers: &reqwest::header::HeaderMap, name: &str) -> Option<u32> {
    headers.get(name)?.to_str().ok()?.parse().ok()
}

/// Parse a duration from a header value. Handles:
/// - Plain seconds: "60"
/// - Duration strings: "1m30s", "2m", "30s"
fn parse_header_duration(headers: &reqwest::header::HeaderMap, name: &str) -> Option<Duration> {
    let val = headers.get(name)?.to_str().ok()?;

    // Try plain seconds first.
    if let Ok(secs) = val.parse::<f64>() {
        return Some(Duration::from_secs_f64(secs));
    }

    // Try duration string: e.g. "1m30s", "2m", "500ms"
    parse_duration_string(val)
}

fn parse_duration_string(s: &str) -> Option<Duration> {
    let mut total = Duration::ZERO;
    let mut num_buf = String::new();
    let chars: Vec<char> = s.chars().collect();
    let mut i = 0;

    while i < chars.len() {
        let ch = chars[i];
        if ch.is_ascii_digit() || ch == '.' {
            num_buf.push(ch);
            i += 1;
        } else {
            if num_buf.is_empty() {
                i += 1;
                continue;
            }
            let n: f64 = num_buf.parse().ok()?;
            num_buf.clear();
            // Look ahead for "ms" (milliseconds) vs bare "m" (minutes).
            if ch == 'm' && i + 1 < chars.len() && chars[i + 1] == 's' {
                total += Duration::from_secs_f64(n / 1000.0);
                i += 2; // skip 'm' and 's'
            } else {
                match ch {
                    'h' => total += Duration::from_secs_f64(n * 3600.0),
                    'm' => total += Duration::from_secs_f64(n * 60.0),
                    's' => total += Duration::from_secs_f64(n),
                    _ => {}
                }
                i += 1;
            }
        }
    }

    if total > Duration::ZERO {
        Some(total)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_plain_seconds() {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert("retry-after", "60".parse().unwrap());
        let d = parse_header_duration(&headers, "retry-after").unwrap();
        assert_eq!(d, Duration::from_secs(60));
    }

    #[test]
    fn parse_duration_str() {
        assert_eq!(
            parse_duration_string("1m30s"),
            Some(Duration::from_secs(90))
        );
        assert_eq!(
            parse_duration_string("2m"),
            Some(Duration::from_secs(120))
        );
    }

    #[test]
    fn parse_milliseconds() {
        assert_eq!(
            parse_duration_string("500ms"),
            Some(Duration::from_millis(500))
        );
        assert_eq!(
            parse_duration_string("100ms"),
            Some(Duration::from_millis(100))
        );
    }

    #[test]
    fn parse_mixed_minutes_and_milliseconds() {
        // "1m500ms" = 60s + 0.5s = 60.5s
        let d = parse_duration_string("1m500ms").unwrap();
        assert!((d.as_secs_f64() - 60.5).abs() < 0.001);
    }

    #[test]
    fn tracker_availability() {
        let tracker = RateLimitTracker::new();
        assert!(tracker.is_available(&Provider::Groq));

        tracker.mark_rate_limited(&Provider::Groq, Duration::from_secs(60));
        assert!(!tracker.is_available(&Provider::Groq));

        tracker.clear(&Provider::Groq);
        assert!(tracker.is_available(&Provider::Groq));
    }
}
