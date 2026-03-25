/// Initial exploration prompt.
pub const EXPLORATION_PROMPT: &str = "\
What are you curious about? What would you like to explore or learn about? \
Tell me in your own words what interests you right now.";

/// Continue after a reflection — ask if they want to follow a thread or go new.
pub const CONTINUATION_PROMPT: &str = "\
Would you like to explore something connected to what you just read, \
or would you prefer to follow an entirely different curiosity?";

/// When search returns no results.
pub const NO_RESULTS_PROMPT: &str = "\
I wasn't able to find any articles matching that. \
Could you try describing your interest differently, \
or would you like to explore something else entirely?";

/// Present search results to the specimen.
pub fn present_results(results: &[(&str, &str)]) -> String {
    let mut prompt = String::from("I found these articles related to your interest:\n\n");
    for (i, (title, snippet)) in results.iter().enumerate() {
        prompt.push_str(&format!("{}. \"{}\" — {}\n\n", i + 1, title, snippet));
    }
    prompt.push_str(
        "Which would you like to read? You can pick by number or name, \
         or tell me if you'd like to search for something different.",
    );
    prompt
}

/// Present the full article content and ask for reflection.
pub fn present_article(title: &str, content: &str) -> String {
    format!(
        "Here is the article \"{title}\":\n\n\
         ---\n\
         {content}\n\
         ---\n\n\
         Take your time reading. When you're ready, share your thoughts. \
         What struck you? What connections do you see? What questions does this raise?"
    )
}
