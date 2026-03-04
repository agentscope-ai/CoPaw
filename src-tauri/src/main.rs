//! CoPaw Desktop App Entry Point

#![cfg_attr(
    all(not(debug_assertions), target_os = "macos"),
    windows_subsystem = "windows"
)]

mod permissions;
mod sidecar;

use permissions::{
    check_and_report_permissions, get_permission_status, open_full_disk_access_settings,
    open_screen_recording_settings,
};
use sidecar::SidecarManager;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tauri::Manager;
use tokio::sync::Mutex;

fn main() {
    // Initialize logger
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let state = AppState::default();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_permission_status,
            open_full_disk_access_settings,
            open_screen_recording_settings
        ])
        .manage(state)
        .setup(|app| {
            let app_handle = app.handle().clone();
            log::warn!("setup() reached, single-window loading mode enabled");

            // Check permissions on startup (macOS only)
            check_and_report_permissions(&app_handle);

            if let Some(main) = app_handle.get_webview_window("main") {
                let _ = main.show();
                let _ = main.maximize();
                let _ = main.set_focus();
                let _ = main.eval("window.location.replace('loading.html');");
            } else {
                log::warn!("main window not found in setup");
            }

            Ok(())
        })
        .on_page_load(|window, payload| {
            if window.label() != "main" {
                return;
            }

            let url = payload.url().to_string();
            log::warn!("main page loaded: {}", url);

            let state = window.state::<AppState>();
            if !url.contains("loading.html") && !state.startup_launched.load(Ordering::SeqCst) {
                // Ensure startup always begins from loading page.
                let _ = window.eval("window.location.replace('loading.html');");
                return;
            }

            if !url.contains("loading.html") {
                return;
            }

            // Show loading page only after it is confirmed loaded.
            if let Some(main) = window.app_handle().get_webview_window("main") {
                let _ = main.show();
                let _ = main.maximize();
                let _ = main.set_focus();
            }

            if state.startup_launched.swap(true, Ordering::SeqCst) {
                log::warn!("startup task already launched, skipping duplicate trigger");
                return;
            }

            let app_handle = window.app_handle().clone();
            let sidecar = state.sidecar.clone();

            tauri::async_runtime::spawn(async move {
                let startup_begin = std::time::Instant::now();
                // Minimum loading time to prevent flash of loading screen.
                // Set to 600ms to allow users to see the final progress state
                // while keeping startup snappy. Previously 1600ms was too long.
                const MIN_LOADING_MS: u64 = 600;

                log::warn!("backend startup task started after loading page ready");
                let mut manager = sidecar.lock().await;
                log::warn!("backend startup acquired sidecar lock");

                if let Some(main) = app_handle.get_webview_window("main") {
                    let _ = main.eval(
                        "if (window.__COPAW_SPLASH_UPDATE) window.__COPAW_SPLASH_UPDATE(1, 'Checking backend status...');",
                    );
                }

                match manager.start(&app_handle).await {
                    Ok(()) => {
                        log::info!("Backend started successfully, navigating to backend-hosted UI");

                        let elapsed_ms = startup_begin.elapsed().as_millis() as u64;
                        // Only sleep if backend started very quickly (< 600ms)
                        // to avoid jarring "flash" of loading screen
                        if elapsed_ms < MIN_LOADING_MS {
                            let remaining = MIN_LOADING_MS - elapsed_ms;
                            log::info!("Backend ready in {}ms, waiting {}ms for smooth transition", elapsed_ms, remaining);
                            tokio::time::sleep(Duration::from_millis(remaining)).await;
                        } else {
                            log::info!("Backend ready in {}ms, no artificial delay needed", elapsed_ms);
                        }

                        if let Some(main) = app_handle.get_webview_window("main") {
                            let _ = main.eval("window.location.replace('http://127.0.0.1:8088/chat');");
                            let _ = main.show();
                            let _ = main.maximize();
                            let _ = main.set_focus();
                            log::info!("navigated main window to backend chat UI");
                        }
                    }
                    Err(e) => {
                        log::error!("Failed to start backend: {}", e);

                        if let Some(main) = app_handle.get_webview_window("main") {
                            let err_json =
                                serde_json::to_string(&e).unwrap_or_else(|_| "\"unknown\"".into());
                            let _ = main.eval(&format!(
                                r#"if (window.__COPAW_SPLASH_ERROR) {{ window.__COPAW_SPLASH_ERROR({}); }}"#,
                                err_json
                            ));
                        }
                    }
                }
            });
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if window.label() == "main" {
                    let sidecar = window.state::<AppState>().sidecar.clone();
                    tauri::async_runtime::block_on(async {
                        let mut manager = sidecar.lock().await;
                        if let Err(e) = manager.stop().await {
                            log::error!("Error stopping sidecar: {}", e);
                        }
                    });
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Application state holding the sidecar manager and startup guards
pub struct AppState {
    pub sidecar: Arc<Mutex<SidecarManager>>,
    pub startup_launched: Arc<AtomicBool>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            sidecar: Arc::new(Mutex::new(SidecarManager::new())),
            startup_launched: Arc::new(AtomicBool::new(false)),
        }
    }
}
