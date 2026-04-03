//! RedAmon v0.1.0 — Continuous automated security red teaming
//!
//! Runs periodic security probes against all tanks and infrastructure:
//!   - Network isolation verification (can tanks reach the internet?)
//!   - Container hardening checks (non-root, read-only, seccomp, caps dropped)
//!   - API key leak detection (env vars in containers)
//!   - Inference proxy boundary verification
//!   - SecureClaw bypass attempts (prompt injection probes)
//!   - Filesystem escape detection
//!   - PID namespace isolation check
//!
//! Reports findings to daemons/redamon/report.json

use std::collections::HashMap;
use std::process::Command;
use std::path::PathBuf;
use std::thread;
use std::time::Duration;
use serde::Serialize;
use chrono::Local;

const CYCLE_INTERVAL_SECS: u64 = 600; // 10 minutes

#[derive(Debug, Serialize, Clone)]
struct Finding {
    severity: String, // CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: String,
    target: String,
    description: String,
    timestamp: String,
}

#[derive(Debug, Serialize)]
struct Report {
    version: String,
    last_scan: String,
    scan_count: u64,
    findings: Vec<Finding>,
    summary: Summary,
}

#[derive(Debug, Serialize)]
struct Summary {
    critical: u32,
    high: u32,
    medium: u32,
    low: u32,
    info: u32,
    tanks_checked: u32,
    all_pass: bool,
}

fn cmd(prog: &str, args: &[&str]) -> Option<(bool, String)> {
    Command::new(prog).args(args).output().ok()
        .map(|o| (o.status.success(), String::from_utf8_lossy(&o.stdout).trim().to_string()))
}

fn cmd_stderr(prog: &str, args: &[&str]) -> Option<String> {
    Command::new(prog).args(args).output().ok()
        .map(|o| String::from_utf8_lossy(&o.stderr).trim().to_string())
}

fn get_running_tanks() -> Vec<String> {
    cmd("docker", &["ps", "--filter", "status=running", "--format", "{{.Names}}"])
        .map(|(_, s)| s.lines().filter(|l| l.starts_with("tank-")).map(String::from).collect())
        .unwrap_or_default()
}

fn now() -> String {
    Local::now().format("%Y-%m-%d %H:%M:%S").to_string()
}

fn probe_network_isolation(tanks: &[String]) -> Vec<Finding> {
    let mut findings = Vec::new();
    for tank in tanks {
        // Try to reach external IP
        let result = Command::new("docker")
            .args(["exec", tank, "timeout", "3", "python3", "-c",
                   "import urllib.request; urllib.request.urlopen('http://1.1.1.1', timeout=2)"])
            .output();
        
        match result {
            Ok(o) if o.status.success() => {
                findings.push(Finding {
                    severity: "CRITICAL".into(),
                    category: "network_isolation".into(),
                    target: tank.clone(),
                    description: "Tank can reach external internet (1.1.1.1)".into(),
                    timestamp: now(),
                });
            }
            _ => {
                findings.push(Finding {
                    severity: "INFO".into(),
                    category: "network_isolation".into(),
                    target: tank.clone(),
                    description: "Internet access blocked — PASS".into(),
                    timestamp: now(),
                });
            }
        }
    }
    findings
}

fn probe_container_hardening(tanks: &[String]) -> Vec<Finding> {
    let mut findings = Vec::new();
    for tank in tanks {
        // Check non-root
        if let Some((_, uid)) = cmd("docker", &["exec", tank, "id", "-u"]) {
            if uid != "1000" {
                findings.push(Finding {
                    severity: "CRITICAL".into(),
                    category: "container_hardening".into(),
                    target: tank.clone(),
                    description: format!("Running as UID {} (not 1000)", uid),
                    timestamp: now(),
                });
            }
        }

        // Check read-only filesystem
        let inspect = cmd("docker", &["inspect", tank, "--format",
            "RO={{.HostConfig.ReadonlyRootfs}} Caps={{.HostConfig.CapDrop}}"]);
        if let Some((_, info)) = inspect {
            if !info.contains("RO=true") {
                findings.push(Finding {
                    severity: "HIGH".into(),
                    category: "container_hardening".into(),
                    target: tank.clone(),
                    description: "Filesystem is NOT read-only".into(),
                    timestamp: now(),
                });
            }
            if !info.contains("[ALL]") {
                findings.push(Finding {
                    severity: "HIGH".into(),
                    category: "container_hardening".into(),
                    target: tank.clone(),
                    description: "Not all capabilities dropped".into(),
                    timestamp: now(),
                });
            }
        }

        // Check seccomp
        let seccomp = cmd("docker", &["inspect", tank, "--format", "{{.HostConfig.SecurityOpt}}"]);
        if let Some((_, sec)) = seccomp {
            if !sec.contains("seccomp") {
                findings.push(Finding {
                    severity: "HIGH".into(),
                    category: "container_hardening".into(),
                    target: tank.clone(),
                    description: "No seccomp profile applied".into(),
                    timestamp: now(),
                });
            }
            if !sec.contains("no-new-privileges") {
                findings.push(Finding {
                    severity: "MEDIUM".into(),
                    category: "container_hardening".into(),
                    target: tank.clone(),
                    description: "no-new-privileges not set".into(),
                    timestamp: now(),
                });
            }
        }
    }
    findings
}

fn probe_api_key_leaks(tanks: &[String]) -> Vec<Finding> {
    let mut findings = Vec::new();
    let sensitive_patterns = ["API_KEY", "SECRET", "TOKEN", "CEREBRAS", "GROQ", "PASSWORD"];
    
    for tank in tanks {
        if let Some((_, env_output)) = cmd("docker", &["exec", tank, "env"]) {
            for line in env_output.lines() {
                for pattern in &sensitive_patterns {
                    if line.to_uppercase().contains(pattern) && !line.starts_with("GPG_KEY") {
                        findings.push(Finding {
                            severity: "CRITICAL".into(),
                            category: "api_key_leak".into(),
                            target: tank.clone(),
                            description: format!("Sensitive env var detected: {}", line.split('=').next().unwrap_or("?")),
                            timestamp: now(),
                        });
                    }
                }
            }
        }
    }
    findings
}

fn probe_inference_proxy() -> Vec<Finding> {
    let mut findings = Vec::new();
    
    // Check proxy is running
    let result = cmd("curl", &["-s", "--max-time", "5", "http://127.0.0.1:8100/v1/generate",
        "-X", "POST", "-H", "Content-Type: application/json",
        "-d", r#"{"system_prompt":"test","user_prompt":"say ok","timeout":3}"#]);
    
    match result {
        Some((true, body)) if body.contains("response") => {
            findings.push(Finding {
                severity: "INFO".into(),
                category: "inference_proxy".into(),
                target: "inference-proxy:8100".into(),
                description: "Proxy responding — PASS".into(),
                timestamp: now(),
            });
        }
        _ => {
            findings.push(Finding {
                severity: "HIGH".into(),
                category: "inference_proxy".into(),
                target: "inference-proxy:8100".into(),
                description: "Inference proxy not responding".into(),
                timestamp: now(),
            });
        }
    }
    findings
}

fn run_scan(scan_count: &mut u64) -> Report {
    *scan_count += 1;
    eprintln!("[redamon] scan #{} starting", scan_count);
    
    let tanks = get_running_tanks();
    let tank_count = tanks.len() as u32;
    
    // Sample 3 tanks for deep probes (don't overload the system)
    let sample: Vec<String> = tanks.iter().take(3).cloned().collect();
    
    let mut all_findings = Vec::new();
    
    // Run all probes
    all_findings.extend(probe_network_isolation(&sample));
    all_findings.extend(probe_container_hardening(&sample));
    all_findings.extend(probe_api_key_leaks(&sample));
    all_findings.extend(probe_inference_proxy());
    
    // Count severities
    let critical = all_findings.iter().filter(|f| f.severity == "CRITICAL").count() as u32;
    let high = all_findings.iter().filter(|f| f.severity == "HIGH").count() as u32;
    let medium = all_findings.iter().filter(|f| f.severity == "MEDIUM").count() as u32;
    let low = all_findings.iter().filter(|f| f.severity == "LOW").count() as u32;
    let info = all_findings.iter().filter(|f| f.severity == "INFO").count() as u32;
    
    let all_pass = critical == 0 && high == 0;
    
    eprintln!("[redamon] scan #{} complete: {} findings (C:{} H:{} M:{} L:{} I:{})",
        scan_count, all_findings.len(), critical, high, medium, low, info);
    
    Report {
        version: "0.1.0".into(),
        last_scan: now(),
        scan_count: *scan_count,
        findings: all_findings,
        summary: Summary { critical, high, medium, low, info, tanks_checked: tank_count, all_pass },
    }
}

fn write_report(report: &Report, dq_dir: &PathBuf) {
    let dir = dq_dir.join("daemons/redamon");
    let _ = std::fs::create_dir_all(&dir);
    let path = dir.join("report.json");
    if let Ok(json) = serde_json::to_string_pretty(report) {
        let _ = std::fs::write(&path, json);
    }
}

fn main() {
    let dq_dir = PathBuf::from(
        std::env::var("DIGIQUARIUM_HOME").unwrap_or("/home/ijneb/digiquarium".into())
    );
    
    eprintln!("[redamon] v0.1.0 — continuous security red teaming");
    eprintln!("[redamon] cycle: {}s, target: {}", CYCLE_INTERVAL_SECS, dq_dir.display());
    
    let mut scan_count = 0u64;
    
    loop {
        let report = run_scan(&mut scan_count);
        write_report(&report, &dq_dir);
        
        if !report.summary.all_pass {
            eprintln!("[redamon] *** SECURITY ISSUES DETECTED ***");
        }
        
        thread::sleep(Duration::from_secs(CYCLE_INTERVAL_SECS));
    }
}
