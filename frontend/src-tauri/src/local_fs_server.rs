use rand::Rng;
use serde_json::json;
use std::sync::OnceLock;

use crate::commands::local_fs;

/// Port the local-fs server ended up binding to.
static LOCAL_FS_PORT: OnceLock<u16> = OnceLock::new();

/// Random bearer token generated once at startup.
static LOCAL_FS_TOKEN: OnceLock<String> = OnceLock::new();

pub fn get_port() -> Option<u16> {
    LOCAL_FS_PORT.get().copied()
}

pub fn get_token() -> Option<&'static str> {
    LOCAL_FS_TOKEN.get().map(|s| s.as_str())
}

/// Generate a 32-byte hex token using the `rand` crate.
fn generate_token() -> String {
    let mut rng = rand::thread_rng();
    let bytes: [u8; 32] = rng.gen();
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

/// Start the local-fs HTTP server on the first available port in 19200..19299.
/// Runs in a background thread; returns the bound port.
pub fn start_server() -> u16 {
    let token = generate_token();
    LOCAL_FS_TOKEN
        .set(token)
        .expect("LOCAL_FS_TOKEN already initialised");

    let (port, server) = bind_server();
    LOCAL_FS_PORT
        .set(port)
        .expect("LOCAL_FS_PORT already initialised");

    std::thread::spawn(move || {
        loop {
            match server.recv() {
                Ok(mut request) => {
                    let url = request.url().to_string();
                    let method = request.method().to_string();

                    if method != "POST" {
                        let body = json!({"error": "Only POST is supported"}).to_string();
                        let resp = tiny_http::Response::from_string(body)
                            .with_status_code(405)
                            .with_header(
                                tiny_http::Header::from_bytes(
                                    &b"Content-Type"[..],
                                    &b"application/json"[..],
                                )
                                .unwrap(),
                            );
                        let _ = request.respond(resp);
                        continue;
                    }

                    // Authenticate request
                    let expected_token = LOCAL_FS_TOKEN.get().map(|s| s.as_str()).unwrap_or("");
                    let auth_ok = request.headers().iter().any(|h| {
                        h.field.as_str().to_ascii_lowercase() == "authorization"
                            && h.value.as_str() == format!("Bearer {}", expected_token)
                    });
                    if expected_token.is_empty() || !auth_ok {
                        let body = json!({"error": "Unauthorized"}).to_string();
                        let resp = tiny_http::Response::from_string(body)
                            .with_status_code(401)
                            .with_header(
                                tiny_http::Header::from_bytes(
                                    &b"Content-Type"[..],
                                    &b"application/json"[..],
                                )
                                .unwrap(),
                            );
                        let _ = request.respond(resp);
                        continue;
                    }

                    // Read request body
                    let mut body = String::new();
                    let _ = request.as_reader().read_to_string(&mut body);

                    let result = handle_route(&url, &body);
                    let (status, resp_body) = match result {
                        Ok(v) => (200, v),
                        Err(e) => {
                            let err = json!({"error": e}).to_string();
                            (400, err)
                        }
                    };

                    let resp = tiny_http::Response::from_string(resp_body)
                        .with_status_code(status)
                        .with_header(
                            tiny_http::Header::from_bytes(
                                &b"Content-Type"[..],
                                &b"application/json"[..],
                            )
                            .unwrap(),
                        );
                    let _ = request.respond(resp);
                }
                Err(e) => {
                    eprintln!("[LocalFS] Server error: {}", e);
                    break;
                }
            }
        }
    });

    port
}

fn bind_server() -> (u16, tiny_http::Server) {
    for port in 19200u16..19300 {
        let addr = format!("127.0.0.1:{}", port);
        match tiny_http::Server::http(&addr) {
            Ok(server) => {
                println!("[LocalFS] Server listening on {}", addr);
                return (port, server);
            }
            Err(_) => continue,
        }
    }
    panic!("[LocalFS] Failed to bind any port in 19200..19299");
}

fn handle_route(url: &str, body: &str) -> Result<String, String> {
    let value: serde_json::Value =
        serde_json::from_str(body).map_err(|e| format!("Invalid JSON body: {}", e))?;

    match url {
        "/api/local-fs/read" => {
            let path = value["path"]
                .as_str()
                .ok_or("Missing 'path' field")?
                .to_string();
            let encoding = value["encoding"].as_str().map(|s| s.to_string());
            let content = local_fs::read_file_as_text(path, encoding)?;
            Ok(json!({"content": content}).to_string())
        }
        "/api/local-fs/write" => {
            let path = value["path"]
                .as_str()
                .ok_or("Missing 'path' field")?
                .to_string();
            let content = value["content"]
                .as_str()
                .ok_or("Missing 'content' field")?
                .to_string();
            let append = value["append"].as_bool();
            local_fs::write_file(path, content, append)?;
            Ok(json!({"ok": true}).to_string())
        }
        "/api/local-fs/list" => {
            let path = value["path"]
                .as_str()
                .ok_or("Missing 'path' field")?
                .to_string();
            let entries = local_fs::list_directory(path)?;
            Ok(json!({"entries": entries}).to_string())
        }
        "/api/local-fs/metadata" => {
            let path = value["path"]
                .as_str()
                .ok_or("Missing 'path' field")?
                .to_string();
            let meta = local_fs::file_metadata(path)?;
            Ok(serde_json::to_string(&meta).unwrap_or_else(|_| "{}".to_string()))
        }
        _ => Err(format!("Unknown endpoint: {}", url)),
    }
}
