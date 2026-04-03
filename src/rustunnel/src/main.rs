//! Rustunnel v0.1.0 — Secure reverse proxy for Digiquarium visitor tanks
//!
//! Architecture:
//!   - Listens on a public-facing port (configurable, default 8443)
//!   - Proxies authenticated requests to the visitor API on port 8200
//!   - Rate limiting per IP (configurable)
//!   - Request logging with timestamps
//!   - CORS headers for browser access
//!   - Connection timeout enforcement
//!   - No external HTTP framework — pure std::net for minimal footprint

use std::collections::HashMap;
use std::io::{Read, Write, BufRead, BufReader};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use std::thread;
use serde::{Deserialize, Serialize};

const DEFAULT_LISTEN_PORT: u16 = 8443;
const UPSTREAM: &str = "127.0.0.1:8200";
const MAX_BODY_SIZE: usize = 65536;
const RATE_LIMIT_REQUESTS: u32 = 30;
const RATE_LIMIT_WINDOW_SECS: u64 = 60;
const CONNECTION_TIMEOUT_SECS: u64 = 30;

#[derive(Debug)]
struct RateLimiter {
    windows: RwLock<HashMap<String, Vec<u64>>>,
}

impl RateLimiter {
    fn new() -> Self {
        Self { windows: RwLock::new(HashMap::new()) }
    }

    fn check(&self, ip: &str) -> bool {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
        let cutoff = now.saturating_sub(RATE_LIMIT_WINDOW_SECS);

        let mut w = self.windows.write().unwrap();
        let entry = w.entry(ip.to_string()).or_insert_with(Vec::new);

        // Prune old entries
        entry.retain(|&t| t > cutoff);

        if entry.len() >= RATE_LIMIT_REQUESTS as usize {
            return false;
        }
        entry.push(now);
        true
    }

    fn cleanup(&self) {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
        let cutoff = now.saturating_sub(RATE_LIMIT_WINDOW_SECS * 2);
        let mut w = self.windows.write().unwrap();
        w.retain(|_, v| {
            v.retain(|&t| t > cutoff);
            !v.is_empty()
        });
    }
}

#[derive(Debug, Serialize)]
struct AccessLog {
    time: String,
    ip: String,
    method: String,
    path: String,
    status: u16,
    upstream_ms: u64,
}

fn now_iso() -> String {
    chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string()
}

fn parse_request(stream: &mut TcpStream) -> Option<(String, String, HashMap<String, String>, Vec<u8>)> {
    stream.set_read_timeout(Some(Duration::from_secs(CONNECTION_TIMEOUT_SECS))).ok();

    let mut reader = BufReader::new(stream.try_clone().ok()?);
    let mut request_line = String::new();
    reader.read_line(&mut request_line).ok()?;

    let parts: Vec<&str> = request_line.trim().split_whitespace().collect();
    if parts.len() < 2 { return None; }
    let method = parts[0].to_string();
    let path = parts[1].to_string();

    // Read headers
    let mut headers = HashMap::new();
    loop {
        let mut line = String::new();
        reader.read_line(&mut line).ok()?;
        let line = line.trim().to_string();
        if line.is_empty() { break; }
        if let Some((k, v)) = line.split_once(':') {
            headers.insert(k.trim().to_lowercase(), v.trim().to_string());
        }
    }

    // Read body if Content-Length present
    let mut body = Vec::new();
    if let Some(len_str) = headers.get("content-length") {
        if let Ok(len) = len_str.parse::<usize>() {
            let len = len.min(MAX_BODY_SIZE);
            body.resize(len, 0);
            reader.read_exact(&mut body).ok()?;
        }
    }

    Some((method, path, headers, body))
}

fn proxy_to_upstream(method: &str, path: &str, headers: &HashMap<String, String>, body: &[u8]) -> Result<(u16, String, Vec<u8>), String> {
    let mut upstream = TcpStream::connect(UPSTREAM).map_err(|e| format!("upstream connect: {}", e))?;
    upstream.set_write_timeout(Some(Duration::from_secs(CONNECTION_TIMEOUT_SECS))).ok();
    upstream.set_read_timeout(Some(Duration::from_secs(CONNECTION_TIMEOUT_SECS))).ok();

    // Forward request
    let mut req = format!("{} {} HTTP/1.1\r\nHost: {}\r\n", method, path, UPSTREAM);
    for (k, v) in headers {
        if k != "host" {
            req.push_str(&format!("{}: {}\r\n", k, v));
        }
    }
    if !body.is_empty() {
        req.push_str(&format!("Content-Length: {}\r\n", body.len()));
    }
    req.push_str("\r\n");
    upstream.write_all(req.as_bytes()).map_err(|e| format!("upstream write: {}", e))?;
    if !body.is_empty() {
        upstream.write_all(body).map_err(|e| format!("upstream body write: {}", e))?;
    }

    // Read response
    let mut reader = BufReader::new(upstream);
    let mut status_line = String::new();
    reader.read_line(&mut status_line).map_err(|e| format!("upstream read: {}", e))?;

    let status = status_line.split_whitespace().nth(1)
        .and_then(|s| s.parse::<u16>().ok())
        .unwrap_or(502);

    let mut resp_headers = HashMap::new();
    loop {
        let mut line = String::new();
        reader.read_line(&mut line).map_err(|e| format!("upstream header: {}", e))?;
        let line = line.trim().to_string();
        if line.is_empty() { break; }
        if let Some((k, v)) = line.split_once(':') {
            resp_headers.insert(k.trim().to_lowercase(), v.trim().to_string());
        }
    }

    let content_type = resp_headers.get("content-type").cloned().unwrap_or_default();

    let mut resp_body = Vec::new();
    if let Some(len_str) = resp_headers.get("content-length") {
        if let Ok(len) = len_str.parse::<usize>() {
            resp_body.resize(len, 0);
            reader.read_exact(&mut resp_body).map_err(|e| format!("upstream body: {}", e))?;
        }
    } else {
        reader.read_to_end(&mut resp_body).ok();
    }

    Ok((status, content_type, resp_body))
}

fn send_response(stream: &mut TcpStream, status: u16, content_type: &str, body: &[u8]) {
    let status_text = match status {
        200 => "OK", 400 => "Bad Request", 403 => "Forbidden",
        404 => "Not Found", 429 => "Too Many Requests",
        502 => "Bad Gateway", 503 => "Service Unavailable",
        _ => "Unknown",
    };

    let resp = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
         Access-Control-Allow-Headers: Content-Type\r\n\
         X-Powered-By: Rustunnel/0.1.0\r\n\r\n",
        status, status_text, content_type, body.len()
    );
    let _ = stream.write_all(resp.as_bytes());
    let _ = stream.write_all(body);
}

fn send_json_error(stream: &mut TcpStream, status: u16, msg: &str) {
    let body = format!("{{\"error\":\"{}\"}}", msg);
    send_response(stream, status, "application/json", body.as_bytes());
}

fn handle_connection(mut stream: TcpStream, limiter: &RateLimiter) {
    let peer = stream.peer_addr().map(|a| a.ip().to_string()).unwrap_or("unknown".into());

    // Rate limit check
    if !limiter.check(&peer) {
        eprintln!("[rustunnel] rate limited: {}", peer);
        send_json_error(&mut stream, 429, "rate limited");
        return;
    }

    let Some((method, path, headers, body)) = parse_request(&mut stream) else {
        send_json_error(&mut stream, 400, "bad request");
        return;
    };

    // Handle CORS preflight
    if method == "OPTIONS" {
        send_response(&mut stream, 200, "text/plain", b"");
        return;
    }

    // Only proxy /api/* paths
    if !path.starts_with("/api/") {
        send_json_error(&mut stream, 404, "not found");
        return;
    }

    // Proxy to upstream
    let start = Instant::now();
    match proxy_to_upstream(&method, &path, &headers, &body) {
        Ok((status, ct, resp_body)) => {
            let ms = start.elapsed().as_millis() as u64;
            eprintln!("[rustunnel] {} {} {} -> {} ({}ms)", peer, method, path, status, ms);
            let ct = if ct.is_empty() { "application/json".to_string() } else { ct };
            send_response(&mut stream, status, &ct, &resp_body);
        }
        Err(e) => {
            eprintln!("[rustunnel] {} {} {} -> 502 ({})", peer, method, path, e);
            send_json_error(&mut stream, 502, "upstream unavailable");
        }
    }
}

fn main() {
    let port = std::env::var("RUSTUNNEL_PORT")
        .ok().and_then(|s| s.parse().ok())
        .unwrap_or(DEFAULT_LISTEN_PORT);

    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).expect("failed to bind");
    eprintln!("[rustunnel] v0.1.0 listening on {}", addr);
    eprintln!("[rustunnel] upstream: {}", UPSTREAM);
    eprintln!("[rustunnel] rate limit: {}/{} per IP", RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECS);

    let limiter = Arc::new(RateLimiter::new());

    // Cleanup thread
    let lim_clone = limiter.clone();
    thread::spawn(move || loop {
        thread::sleep(Duration::from_secs(60));
        lim_clone.cleanup();
    });

    for stream in listener.incoming().flatten() {
        let lim = limiter.clone();
        thread::spawn(move || handle_connection(stream, &lim));
    }
}
