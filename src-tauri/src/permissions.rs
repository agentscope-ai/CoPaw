//! macOS Permission Management
//!
//! This module handles permission checks and requests for macOS-specific features:
//! - Full Disk Access (for iMessage chat.db access)
//! - Screen Recording (for screenshot features)
//! - Apple Events (for automation)

use std::process::Command;
use tauri::Emitter;

/// Check if the app has Full Disk Access permission
///
/// On macOS, accessing ~/Library/Messages/chat.db (iMessage database) requires
/// Full Disk Access permission. This function checks if the permission is granted
/// by attempting to read a protected file.
#[cfg(target_os = "macos")]
pub fn check_full_disk_access() -> bool {
    // Try to access a file that requires Full Disk Access
    // The Messages database is a good indicator
    let test_path = home::home_dir()
        .unwrap_or_default()
        .join("Library/Messages/chat.db");

    test_path.exists() && std::fs::metadata(&test_path).is_ok()
}

/// Fallback for non-macOS platforms
#[cfg(not(target_os = "macos"))]
pub fn check_full_disk_access() -> bool {
    // On non-macOS, we assume file access works normally
    true
}

/// Check if the app has Screen Recording permission (macOS only)
///
/// Screen recording permission is required for taking screenshots.
/// This check uses tccutil to query the permission status.
#[cfg(target_os = "macos")]
pub fn check_screen_recording() -> bool {
    // Use tccutil to check screen recording permission
    let output = Command::new("tccutil")
        .args(["info", "ScreenCapture"])
        .output();

    match output {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            // If authorized, the output will contain "Authorized" or similar
            stdout.contains("Authorized") || stdout.contains("allowed")
        }
        Err(_) => false,
    }
}

/// Fallback for non-macOS platforms
#[cfg(not(target_os = "macos"))]
pub fn check_screen_recording() -> bool {
    // On non-macOS, we assume screenshot works normally
    true
}

/// Open System Preferences to the Full Disk Access section (macOS only)
#[cfg(target_os = "macos")]
pub fn request_full_disk_access() {
    // Open System Preferences > Privacy & Security > Full Disk Access
    let _ = Command::new("open")
        .arg("x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles")
        .spawn();
}

/// Fallback for non-macOS platforms
#[cfg(not(target_os = "macos"))]
pub fn request_full_disk_access() {
    // No-op on non-macOS
}

/// Open System Preferences to the Screen Recording section (macOS only)
#[cfg(target_os = "macos")]
pub fn request_screen_recording() {
    // Open System Preferences > Privacy & Security > Screen Recording
    let _ = Command::new("open")
        .arg("x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture")
        .spawn();
}

/// Fallback for non-macOS platforms
#[cfg(not(target_os = "macos"))]
pub fn request_screen_recording() {
    // No-op on non-macOS
}

/// Check all permissions and emit events to the frontend
pub fn check_and_report_permissions(app_handle: &tauri::AppHandle) {
    let full_disk_access = check_full_disk_access();
    let screen_recording = check_screen_recording();

    log::info!(
        "Permission check: Full Disk Access={}, Screen Recording={}",
        full_disk_access,
        screen_recording
    );

    // Emit events for the frontend to consume
    let _ = app_handle.emit(
        "permission-status",
        serde_json::json!({
            "full_disk_access": full_disk_access,
            "screen_recording": screen_recording,
            "platform": std::env::consts::OS,
        }),
    );

    // Log warnings for missing permissions
    if !full_disk_access {
        log::warn!(
            "Full Disk Access not granted. iMessage channel and some file operations may not work."
        );
        log::warn!("To fix: Open System Preferences > Privacy & Security > Full Disk Access, then enable CoPaw");
    }

    if !screen_recording {
        log::warn!("Screen Recording permission not granted. Screenshot features will not work.");
        log::warn!("To fix: Open System Preferences > Privacy & Security > Screen Recording, then enable CoPaw");
    }
}

/// Register Tauri commands for permission management
#[tauri::command]
pub fn get_permission_status() -> PermissionStatus {
    PermissionStatus {
        full_disk_access: check_full_disk_access(),
        screen_recording: check_screen_recording(),
        platform: std::env::consts::OS.to_string(),
    }
}

#[tauri::command]
pub fn open_full_disk_access_settings() {
    request_full_disk_access();
}

#[tauri::command]
pub fn open_screen_recording_settings() {
    request_screen_recording();
}

/// Permission status struct for frontend communication
#[derive(serde::Serialize, Clone)]
pub struct PermissionStatus {
    pub full_disk_access: bool,
    pub screen_recording: bool,
    pub platform: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_full_disk_access() {
        let result = check_full_disk_access();
        log::info!("Full disk access check result: {}", result);
    }

    #[test]
    #[cfg(target_os = "macos")]
    fn test_check_screen_recording() {
        let result = check_screen_recording();
        log::info!("Screen recording check result: {}", result);
    }
}
