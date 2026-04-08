use std::fmt;

/// Errors that can occur during remote inference.
#[derive(Debug)]
pub enum RemoteError {
    /// HTTP request failed (connection, timeout, TLS, etc.)
    Http(reqwest::Error),

    /// API returned a structured error response.
    Api {
        status: u16,
        message: String,
        error_type: Option<String>,
        provider: String,
    },

    /// Rate limited by provider (HTTP 429).
    RateLimited {
        provider: String,
        retry_after: Option<std::time::Duration>,
    },

    /// All providers in the router were exhausted (rate-limited or errored).
    AllProvidersExhausted {
        /// Each entry is (provider name, the error that occurred).
        errors: Vec<(String, RemoteError)>,
    },

    /// Invalid configuration (bad model name, missing fields, etc.)
    Config(String),

    /// JSON serialisation or deserialisation failed.
    Json(serde_json::Error),

    /// Error parsing the SSE event stream.
    Stream(String),

    /// Required API key environment variable is not set.
    MissingApiKey {
        env_var: String,
        provider: String,
    },
}

impl fmt::Display for RemoteError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Http(e) => write!(f, "HTTP error: {e}"),
            Self::Api { status, message, provider, .. } => {
                write!(f, "{provider} API error ({status}): {message}")
            }
            Self::RateLimited { provider, retry_after } => {
                write!(f, "{provider} rate limited")?;
                if let Some(d) = retry_after {
                    write!(f, " (retry after {:.1}s)", d.as_secs_f64())?;
                }
                Ok(())
            }
            Self::AllProvidersExhausted { errors } => {
                write!(f, "all providers exhausted:")?;
                for (name, err) in errors {
                    write!(f, "\n  {name}: {err}")?;
                }
                Ok(())
            }
            Self::Config(msg) => write!(f, "config error: {msg}"),
            Self::Json(e) => write!(f, "JSON error: {e}"),
            Self::Stream(msg) => write!(f, "stream error: {msg}"),
            Self::MissingApiKey { env_var, provider } => {
                write!(f, "{provider}: API key env var ${env_var} is not set")
            }
        }
    }
}

impl std::error::Error for RemoteError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Http(e) => Some(e),
            Self::Json(e) => Some(e),
            _ => None,
        }
    }
}

impl From<reqwest::Error> for RemoteError {
    fn from(e: reqwest::Error) -> Self {
        Self::Http(e)
    }
}

impl From<serde_json::Error> for RemoteError {
    fn from(e: serde_json::Error) -> Self {
        Self::Json(e)
    }
}

/// Whether an HTTP status code indicates a transient failure that the router
/// should handle by trying the next provider.
pub(crate) fn is_retryable_status(status: u16) -> bool {
    matches!(status, 429 | 500 | 502 | 503)
}
