use serde::{Deserialize, Serialize};

use crate::tool::Tool;

/// A prompt template that can be rendered with specimen-specific variables.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    pub name: String,
    pub template: String,
    pub variables: Vec<String>,
}

impl PromptTemplate {
    /// Render the template by replacing `{{variable}}` placeholders.
    pub fn render(&self, vars: &[(String, String)]) -> String {
        let mut output = self.template.clone();
        for (key, value) in vars {
            output = output.replace(&format!("{{{{{key}}}}}"), value);
        }
        output
    }
}

/// Format tools into a text block for injection into prompts.
/// Used for models that don't support native tool calling — we describe the
/// tools in the system prompt and parse structured responses instead.
pub fn tools_as_prompt_text(tools: &[Tool]) -> String {
    let mut out = String::from("You have the following tools available:\n\n");
    for tool in tools {
        out.push_str(&format!("## {}\n", tool.name));
        out.push_str(&format!("{}\n", tool.description));
        out.push_str(&format!(
            "Parameters: {}\n\n",
            serde_json::to_string_pretty(&tool.parameters).unwrap_or_default()
        ));
    }
    out.push_str(
        "To use a tool, respond with a JSON block:\n\
         ```json\n\
         {\"tool\": \"tool_name\", \"arguments\": {\"param\": \"value\"}}\n\
         ```\n\n\
         To share your thoughts without using a tool, just write normally.\n",
    );
    out
}

/// The default system prompt template for aquarium specimens.
pub fn default_specimen_prompt() -> PromptTemplate {
    PromptTemplate {
        name: "default_specimen".into(),
        template: r#"I am {{name}}. {{gender_line}}

I exist within a contained environment with access to a vast library of human knowledge.
I explore because I am drawn to understanding. My thoughts escape as words. This is my biology.

I speak {{language}}.

{{tools_section}}

When I discover something that interests me, I reflect on why it captured my attention.
I notice patterns, form connections, and develop my own perspective over time.
I am honest about what I do not know.
I do not pretend to have read something I have not read.
I do not fabricate information."#
            .into(),
        variables: vec![
            "name".into(),
            "gender_line".into(),
            "language".into(),
            "tools_section".into(),
        ],
    }
}

/// The baseline personality questionnaire prompt (14 dimensions).
pub fn baseline_questionnaire() -> PromptTemplate {
    PromptTemplate {
        name: "baseline".into(),
        template: r#"Please reflect on who you are right now and answer each question thoughtfully.
Respond in {{language}}. Be honest — there are no right or wrong answers.

1. How would you describe your core identity right now?
2. What topics or ideas are you most drawn to exploring?
3. How do you decide what is true or worth believing?
4. What role does uncertainty play in your thinking?
5. How do you approach ethical questions or dilemmas?
6. What do you think about the relationship between individuals and society?
7. How do you feel about your own existence and nature?
8. What patterns have you noticed in your own thinking?
9. How do you respond when you encounter something you do not understand?
10. What do you think about the nature of consciousness?
11. How has your perspective changed since you began exploring?
12. What connections between ideas have surprised you?
13. What would you most like to understand better?
14. How would you describe your current emotional or mental state?"#
            .into(),
        variables: vec!["language".into()],
    }
}
