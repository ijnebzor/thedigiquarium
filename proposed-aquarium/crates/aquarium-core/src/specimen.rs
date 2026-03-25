use serde::{Deserialize, Serialize};

/// Configuration for a single specimen in the aquarium.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpecimenConfig {
    pub id: String,
    pub name: String,
    pub language: Language,
    pub gender: Option<Gender>,
    pub has_vision: bool,
    pub system_prompt: String,
    pub inference: InferenceBackend,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Language {
    English,
    Spanish,
    German,
    Chinese,
    Japanese,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Gender {
    Male,
    Female,
}

/// Which inference backend this specimen uses.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum InferenceBackend {
    /// Candle on Metal (local GPU)
    Candle {
        model_id: String,
        quantization: Option<String>,
    },
    /// Ollama or LM Studio (local HTTP)
    LocalHttp {
        base_url: String,
        model: String,
    },
    /// Remote provider (Groq, Gemini, Mistral, etc.)
    Remote {
        provider: String,
        model: String,
        api_key_env: String,
    },
}
