//! CoPaw Desktop App

pub mod sidecar;

use sidecar::SidecarManager;
use std::sync::Arc;
use tokio::sync::Mutex;

/// Application state holding the sidecar manager and permission status
pub struct AppState {
    pub sidecar: Arc<Mutex<SidecarManager>>,
    pub has_full_disk_access: Arc<Mutex<bool>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            sidecar: Arc::new(Mutex::new(SidecarManager::new())),
            has_full_disk_access: Arc::new(Mutex::new(false)),
        }
    }
}
