// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod local_fs_server;

use std::net::TcpStream;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::{ShellExt, process::{CommandChild, CommandEvent}};

struct BackendChild(Arc<Mutex<Option<CommandChild>>>);

fn wait_for_port(port: u16, timeout_secs: u64) -> bool {
    let addr = format!("127.0.0.1:{}", port);
    for _ in 0..(timeout_secs * 2) {
        if TcpStream::connect_timeout(
            &addr.parse().unwrap(),
            Duration::from_millis(500),
        ).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    false
}

fn start_backend(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    // 清理残留的 sidecar 进程（热重载时旧进程可能未退出）
    #[cfg(target_os = "windows")]
    {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/IM", "fugue-backend.exe"])
            .output();
        std::thread::sleep(std::time::Duration::from_millis(500));
    }

    let sidecar = app.shell().sidecar("fugue-backend")?;
    let (mut rx, child) = sidecar.spawn()?;

    // 后台读取 sidecar 输出
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[Backend] {}", String::from_utf8_lossy(&line).trim());
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[Backend] {}", String::from_utf8_lossy(&line).trim());
                }
                CommandEvent::Terminated(status) => {
                    eprintln!("[Backend] Terminated: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
    });

    app.manage(BackendChild(Arc::new(Mutex::new(Some(child)))));
    println!("[Fugue] Sidecar launched, waiting for port 8000...");

    if wait_for_port(8000, 20) {
        println!("[Fugue] Backend ready on port 8000");
    } else {
        eprintln!("[Fugue] Backend did not start within 20s");
    }

    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            commands::local_fs::file_metadata,
            commands::local_fs::read_file_as_text,
            commands::local_fs::read_file_as_base64,
            commands::local_fs::write_file,
            commands::local_fs::list_directory,
            commands::local_fs::save_file_dialog,
            commands::local_fs::pick_folder,
        ])
        .setup(|app| {
            // Start local-fs HTTP server first
            let fs_port = local_fs_server::start_server();
            std::env::set_var("LOCAL_FS_PORT", fs_port.to_string());
            if let Some(token) = local_fs_server::get_token() {
                std::env::set_var("LOCAL_FS_TOKEN", token);
                println!("[Fugue] LocalFS server started on port {} (auth enabled)", fs_port);
            } else {
                println!("[Fugue] LocalFS server started on port {}", fs_port);
            }

            // Then start the backend sidecar
            if let Err(e) = start_backend(app) {
                eprintln!("[Fugue] Sidecar error: {}", e);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                println!("[Fugue] Cleaning up backend...");
                if let Some(state) = window.try_state::<BackendChild>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Fugue");
}
