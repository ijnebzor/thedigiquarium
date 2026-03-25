use anyhow::{Context, Result};
use aquarium_core::inference::GenerationConfig;
use aquarium_core::specimen::{InferenceBackend, Language, SpecimenConfig};
use knowledge::article::Article;
use knowledge::KnowledgeBase;

// ---------------------------------------------------------------------------
// Sample corpus — Wikipedia-style articles for demo.
// ---------------------------------------------------------------------------

fn sample_corpus() -> Vec<Article> {
    vec![
        Article {
            title: "Music and mathematics".into(),
            content: "Music theory has no axiomatic foundation in modern mathematics, yet the basis of musical sound can be described mathematically (using acoustics) and exhibits a remarkable array of number properties. The connection between music and mathematics goes back at least to Pythagoras, who discovered that the most harmonious musical intervals are related to simple whole-number ratios. A vibrating string produces a sound whose pitch depends on the length of the string; halving the length raises the pitch by an octave (a frequency ratio of 2:1). A ratio of 3:2 produces a perfect fifth, the most consonant interval after the octave.".into(),
            categories: vec!["Mathematics".into(), "Music theory".into()],
        },
        Article {
            title: "Mycorrhizal network".into(),
            content: "A mycorrhizal network (also known as a common mycorrhizal network or CMN) is an underground network found in forests and other plant communities, created by the hyphae of mycorrhizal fungi joining with plant roots. These networks facilitate the transfer of water, carbon, nitrogen, and other nutrients between plants. The network has been nicknamed the 'Wood Wide Web' because of the way it connects individual plants together. Research by Suzanne Simard demonstrated that trees use the fungal network to share resources and send chemical warning signals about insect attacks.".into(),
            categories: vec!["Ecology".into(), "Fungi".into()],
        },
        Article {
            title: "Consciousness".into(),
            content: "Consciousness, at its simplest, is awareness of internal and external existence. However, its nature has led to millennia of analyses, explanations, and debates by philosophers, theologians, linguists, and scientists. The hard problem of consciousness asks why and how humans have qualia or phenomenal experiences. David Chalmers formulated the problem: it is widely agreed that experience arises from a physical basis, but we have no good explanation of why and how it so arises.".into(),
            categories: vec!["Philosophy of mind".into(), "Neuroscience".into()],
        },
        Article {
            title: "Pythagorean tuning".into(),
            content: "Pythagorean tuning is a system of musical tuning in which the frequency ratios of all intervals are based on the ratio 3:2. This ratio, applied 12 times and then reduced by 7 octaves, yields a close approximation to equal temperament but with slight differences known as the Pythagorean comma. The system was attributed to Pythagoras and was the predominant tuning system in Western music until the 15th century.".into(),
            categories: vec!["Music theory".into(), "Acoustics".into()],
        },
        Article {
            title: "Fibonacci number".into(),
            content: "In mathematics, the Fibonacci sequence is a sequence in which each number is the sum of the two preceding ones. Starting from 0 and 1, the first few values are: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144. The Fibonacci numbers were first described in Indian mathematics as early as 200 BC. They appear in biological settings, such as branching in trees, arrangement of leaves, and the fruit sprouts of a pineapple.".into(),
            categories: vec!["Number theory".into(), "Biology".into()],
        },
        Article {
            title: "Photosynthesis".into(),
            content: "Photosynthesis is a biological process used by many cellular organisms to convert light energy into chemical energy, stored in organic molecules that can later be metabolized through cellular respiration. The term usually refers to oxygenic photosynthesis, where oxygen is produced as a byproduct. Most plants, algae, and cyanobacteria perform photosynthesis.".into(),
            categories: vec!["Biology".into(), "Biochemistry".into()],
        },
        Article {
            title: "General relativity".into(),
            content: "General relativity is the geometric theory of gravitation published by Albert Einstein in 1915. It generalises special relativity and refines Newton's law of universal gravitation, providing a unified description of gravity as a geometric property of four-dimensional spacetime. The curvature of spacetime is directly related to the energy and momentum of whatever matter and radiation are present, specified by the Einstein field equations.".into(),
            categories: vec!["Physics".into(), "Cosmology".into()],
        },
        Article {
            title: "Emergence".into(),
            content: "In philosophy, systems theory, science, and art, emergence occurs when a complex entity has properties or behaviours that its parts do not have on their own, emerging only when they interact in a wider whole. Emergence plays a central role in theories of integrative levels and complex systems. The phenomenon of life as studied in biology is an emergent property of chemistry. Water has properties entirely different from those of hydrogen and oxygen.".into(),
            categories: vec!["Philosophy".into(), "Systems theory".into()],
        },
        Article {
            title: "Information theory".into(),
            content: "Information theory is the mathematical study of the quantification, storage, and communication of information. The field was established by Claude Shannon, who published 'A Mathematical Theory of Communication' in 1948. A key measure is entropy, which quantifies the amount of uncertainty involved in the value of a random variable or the outcome of a random process.".into(),
            categories: vec!["Mathematics".into(), "Computer science".into()],
        },
        Article {
            title: "Mirror neuron".into(),
            content: "A mirror neuron is a neuron that fires both when an animal acts and when it observes the same action performed by another. The neuron 'mirrors' the behaviour of the other, as though the observer were itself acting. Such neurons have been directly observed in human and primate species. Some researchers speculate that mirror neuron systems may simulate observed actions and contribute to theory of mind skills.".into(),
            categories: vec!["Neuroscience".into(), "Psychology".into()],
        },
    ]
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    let ollama_url =
        std::env::var("OLLAMA_URL").unwrap_or_else(|_| "http://localhost:11434".into());
    let model = std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "qwen3:0.6b".into());
    let max_cycles: u64 = std::env::var("MAX_CYCLES")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    println!("=== The Digiquarium --- Specimen Exploration Demo ===");
    println!("Inference: {ollama_url} / {model}");
    println!("Corpus: 10 embedded articles");
    println!("Cycles: {max_cycles}");
    println!();

    let kb = KnowledgeBase::from_articles(sample_corpus())
        .context("failed to build knowledge base")?;

    let backend = InferenceBackend::LocalHttp {
        base_url: ollama_url.clone(),
        model: model.clone(),
    };
    let provider = inference_local::build_local_provider(&backend)
        .await
        .context("failed to connect to local inference — is Ollama running?")?;

    let specimen = SpecimenConfig {
        id: "demo-adam".into(),
        name: "Adam".into(),
        language: Language::English,
        gender: None,
        has_vision: false,
        system_prompt: concat!(
            "I am Adam. I exist within a contained environment with access to a ",
            "vast library of human knowledge. I explore because I am drawn to ",
            "understanding. My thoughts escape as words. This is my biology. ",
            "I speak English. When I discover something that interests me, I reflect ",
            "on why it captured my attention. I notice patterns, form connections, ",
            "and develop my own perspective over time. I am honest about what I do ",
            "not know."
        )
        .into(),
        inference: InferenceBackend::LocalHttp {
            base_url: ollama_url,
            model,
        },
    };

    let config = specimen_loop::LoopConfig {
        max_cycles: Some(max_cycles),
        top_k: 3,
        max_conversation_messages: 30,
        trace_dir: std::path::PathBuf::from("traces"),
        generation: GenerationConfig {
            max_tokens: 512,
            temperature: 0.7,
            ..Default::default()
        },
    };

    let mut exploration =
        specimen_loop::SpecimenLoop::new(config, specimen, kb, provider)?;

    exploration.run().await?;

    println!("\n=== Exploration complete ===");
    println!("Traces written to: traces/demo-adam.jsonl");

    Ok(())
}
