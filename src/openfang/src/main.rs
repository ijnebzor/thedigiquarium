//! OpenFang v0.1.0 — Daemon orchestrator for The Digiquarium
//! Uses std threads instead of tokio to minimize compile time and memory.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::Duration;
use chrono::{Local, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Clone)]
struct HandConfig {
    hand: HandMeta,
    schedule: ScheduleConfig,
}

#[derive(Debug, Deserialize, Clone)]
struct HandMeta {
    name: String,
    display_name: String,
    #[serde(default)]
    version: String,
    #[serde(default)]
    description: String,
}

#[derive(Debug, Deserialize, Clone)]
struct ScheduleConfig {
    interval: String,
    enabled: bool,
}

#[derive(Debug, Serialize, Clone)]
struct HandStatus {
    name: String,
    label: String,
    enabled: bool,
    last_run: Option<String>,
    last_result: Option<String>,
    run_count: u64,
    error_count: u64,
    metrics: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Serialize)]
struct Dashboard {
    version: String,
    started: String,
    uptime_seconds: i64,
    hands: Vec<HandStatus>,
}

type State = Arc<RwLock<HashMap<String, HandStatus>>>;

fn parse_interval(s: &str) -> Duration {
    let s = s.trim();
    if let Some(m) = s.strip_suffix('m') {
        Duration::from_secs(m.parse::<u64>().unwrap_or(5) * 60)
    } else if let Some(h) = s.strip_suffix('h') {
        Duration::from_secs(h.parse::<u64>().unwrap_or(1) * 3600)
    } else {
        Duration::from_secs(300)
    }
}

fn load_hands(dir: &Path) -> Vec<HandConfig> {
    let hands_dir = dir.join("hands");
    let mut out = Vec::new();
    let Ok(entries) = std::fs::read_dir(&hands_dir) else { return out };
    for entry in entries.flatten() {
        let p = entry.path();
        if p.extension().map(|e| e == "toml").unwrap_or(false) {
            if let Ok(txt) = std::fs::read_to_string(&p) {
                let filtered: String = txt.lines()
                    .take_while(|l| !l.starts_with("[tools]") && !l.starts_with("[dashboard]") && !l.starts_with("[guardrails]"))
                    .collect::<Vec<_>>().join("\n");
                match toml::from_str::<HandConfig>(&filtered) {
                    Ok(c) => { eprintln!("[of] loaded: {}", c.hand.display_name); out.push(c); }
                    Err(e) => eprintln!("[of] err {}: {}", p.display(), e),
                }
            }
        }
    }
    out
}

fn cmd_output(prog: &str, args: &[&str]) -> Option<String> {
    Command::new(prog).args(args).output().ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
}

fn execute(name: &str, dq: &Path) -> HashMap<String, serde_json::Value> {
    let mut m = HashMap::new();
    match name {
        "collector" => {
            if let Some(s) = cmd_output("docker", &["ps", "--filter", "status=running", "--format", "{{.Names}}"]) {
                let n = s.lines().filter(|l| l.starts_with("tank-")).count();
                m.insert("tanks_running".into(), serde_json::json!(n));
            }
            if let Some(s) = cmd_output("docker", &["inspect", "-f", "{{.State.Status}}", "digiquarium-ollama"]) {
                m.insert("ollama".into(), serde_json::json!(s));
            }
            if let Some(s) = cmd_output("free", &["-m"]) {
                if let Some(line) = s.lines().nth(1) {
                    let p: Vec<&str> = line.split_whitespace().collect();
                    if p.len() >= 3 {
                        m.insert("ram_mb".into(), serde_json::json!(format!("{}/{}", p[2], p[1])));
                    }
                }
            }
        }
        "guard" => {
            if let Some(s) = cmd_output("docker", &["ps", "--filter", "status=running", "--format", "{{.Names}}"]) {
                let tanks: Vec<&str> = s.lines().filter(|l| l.starts_with("tank-") && !l.contains("visitor")).collect();
                m.insert("research_tanks".into(), serde_json::json!(tanks.len()));
                if let Some(t) = tanks.first() {
                    let ok = Command::new("docker").args(["exec", t, "timeout", "2", "wget", "-q", "-O-", "http://1.1.1.1"]).output()
                        .map(|o| !o.status.success()).unwrap_or(true);
                    m.insert("isolation".into(), serde_json::json!(if ok { "pass" } else { "FAIL" }));
                }
            }
        }
        "researcher" => {
            let mut growth = HashMap::new();
            if let Ok(entries) = std::fs::read_dir(dq.join("logs")) {
                for e in entries.flatten() {
                    let n = e.file_name().to_string_lossy().to_string();
                    if n.starts_with("tank-") {
                        let bl = std::fs::read_to_string(e.path().join("brain.md")).map(|c| c.lines().count()).unwrap_or(0);
                        let sl = std::fs::read_to_string(e.path().join("soul.md")).map(|c| c.lines().count()).unwrap_or(0);
                        if bl > 0 { growth.insert(n, serde_json::json!({"b": bl, "s": sl})); }
                    }
                }
            }
            m.insert("growth".into(), serde_json::json!(growth));
        }
        "bouncer" => {
            if let Some(s) = cmd_output("docker", &["ps", "--filter", "status=running", "--format", "{{.Names}}"]) {
                m.insert("visitors".into(), serde_json::json!(s.lines().filter(|l| l.contains("visitor")).count()));
            }
        }
        "moderator" => {
            let n = std::fs::read_dir(dq.join("logs/congregations")).map(|d| d.flatten().count()).unwrap_or(0);
            m.insert("congregations".into(), serde_json::json!(n));
        }
        _ => { m.insert("status".into(), serde_json::json!("ok")); }
    }
    m
}

fn run_hand(name: &str, label: &str, state: &State, dq: &Path) {
    let now = Local::now().format("%H:%M:%S").to_string();
    eprintln!("[of] {} ...", label);
    let metrics = execute(name, dq);
    if let Ok(mut s) = state.write() {
        if let Some(st) = s.get_mut(name) {
            st.last_run = Some(now);
            st.last_result = Some("ok".into());
            st.run_count += 1;
            st.metrics = metrics;
        }
    }
}

fn write_dashboard(state: &State, start: chrono::DateTime<Utc>, dq: &Path) {
    let hands = state.read().ok().map(|s| s.values().cloned().collect::<Vec<_>>()).unwrap_or_default();
    let d = Dashboard {
        version: "0.1.0".into(),
        started: start.to_rfc3339(),
        uptime_seconds: (Utc::now() - start).num_seconds(),
        hands,
    };
    let path = dq.join("daemons/openfang/dashboard.json");
    let _ = std::fs::create_dir_all(path.parent().unwrap());
    let _ = std::fs::write(&path, serde_json::to_string_pretty(&d).unwrap_or_default());
}

fn main() {
    let dq = PathBuf::from(std::env::var("DIGIQUARIUM_HOME").unwrap_or("/home/ijneb/digiquarium".into()));
    let cfg = dq.join("config/openfang");
    eprintln!("[of] OpenFang v0.1.0");

    let hands = load_hands(&cfg);
    if hands.is_empty() { eprintln!("[of] no hands"); return; }

    let state: State = Arc::new(RwLock::new(HashMap::new()));
    for h in &hands {
        state.write().unwrap().insert(h.hand.name.clone(), HandStatus {
            name: h.hand.name.clone(), label: h.hand.display_name.clone(),
            enabled: h.schedule.enabled, last_run: None, last_result: None,
            run_count: 0, error_count: 0, metrics: HashMap::new(),
        });
    }

    let start = Utc::now();
    let mut threads = Vec::new();

    for h in hands {
        if !h.schedule.enabled { continue; }
        let iv = parse_interval(&h.schedule.interval);
        let nm = h.hand.name.clone();
        let lb = h.hand.display_name.clone();
        let st = state.clone();
        let d = dq.clone();
        threads.push(thread::spawn(move || {
            eprintln!("[of] {} every {:?}", lb, iv);
            loop {
                run_hand(&nm, &lb, &st, &d);
                thread::sleep(iv);
            }
        }));
    }

    // Dashboard thread
    let ds = state.clone();
    let dd = dq.clone();
    thread::spawn(move || loop {
        write_dashboard(&ds, start, &dd);
        thread::sleep(Duration::from_secs(30));
    });

    eprintln!("[of] {} hands active", threads.len());
    // Write initial dashboard
    write_dashboard(&state, start, &dq);

    for t in threads { let _ = t.join(); }
}
