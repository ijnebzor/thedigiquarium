use serde::{Deserialize, Serialize};

/// A tool that a specimen can invoke.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tool {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
}

/// A tool call parsed from model output.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    /// Unique identifier for correlating with ToolResult. Present for native
    /// tool calls (Ollama, remote APIs); generated for text-parsed calls.
    #[serde(default)]
    pub id: Option<String>,
    pub tool: String,
    pub arguments: serde_json::Value,
}

/// The result of executing a tool call.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    pub tool: String,
    pub content: String,
    pub success: bool,
}

/// The standard tools available to specimens in the aquarium.
pub fn specimen_tools() -> Vec<Tool> {
    vec![
        Tool {
            name: "search".into(),
            description: "Search for Wikipedia articles by keyword. Returns a list of matching article titles and snippets.".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }),
        },
        Tool {
            name: "read".into(),
            description: "Read a Wikipedia article by title. Returns the full article text.".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The exact article title to read"
                    }
                },
                "required": ["title"]
            }),
        },
        Tool {
            name: "explore".into(),
            description: "Browse a random Wikipedia article to discover something new.".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {}
            }),
        },
    ]
}
