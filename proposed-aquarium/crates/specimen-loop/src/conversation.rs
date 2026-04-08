use aquarium_core::inference::{Message, Role};

/// Manages the conversation history for one specimen's exploration session.
pub struct Conversation {
    messages: Vec<Message>,
    max_messages: usize,
}

impl Conversation {
    /// Create a new conversation with the given system prompt.
    pub fn new(system_prompt: &str, max_messages: usize) -> Self {
        Self {
            messages: vec![Message {
                role: Role::System,
                content: system_prompt.to_string(),
            }],
            max_messages,
        }
    }

    /// Add a user (loop engine) message.
    pub fn add_user(&mut self, content: &str) {
        self.messages.push(Message {
            role: Role::User,
            content: content.to_string(),
        });
        self.trim();
    }

    /// Add an assistant (specimen) message.
    pub fn add_assistant(&mut self, content: &str) {
        self.messages.push(Message {
            role: Role::Assistant,
            content: content.to_string(),
        });
        self.trim();
    }

    /// Current message history.
    pub fn messages(&self) -> &[Message] {
        &self.messages
    }

    /// Trim old messages, always keeping the system prompt at index 0.
    fn trim(&mut self) {
        if self.messages.len() > self.max_messages {
            let drain_end = self.messages.len() - self.max_messages + 1;
            if drain_end > 1 {
                self.messages.drain(1..drain_end);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_conversation_has_system_prompt() {
        let c = Conversation::new("You are a specimen.", 10);
        assert_eq!(c.messages().len(), 1);
        assert_eq!(c.messages()[0].role, Role::System);
    }

    #[test]
    fn add_messages() {
        let mut c = Conversation::new("system", 10);
        c.add_user("hello");
        c.add_assistant("hi there");
        assert_eq!(c.messages().len(), 3);
        assert_eq!(c.messages()[1].role, Role::User);
        assert_eq!(c.messages()[2].role, Role::Assistant);
    }

    #[test]
    fn trimming_preserves_system_prompt() {
        let mut c = Conversation::new("system", 4); // system + 3 messages max
        c.add_user("1");
        c.add_assistant("2");
        c.add_user("3");
        c.add_assistant("4"); // should trigger trim
        c.add_user("5");

        assert!(c.messages().len() <= 4);
        assert_eq!(c.messages()[0].role, Role::System);
        assert_eq!(c.messages()[0].content, "system");
    }
}
