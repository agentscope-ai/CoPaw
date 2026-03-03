# macOS DMG packaging

Build from repo root:

```bash
bash scripts/macos/build_dmg.sh [VERSION]
bash scripts/macos/build_dmg.sh [VERSION] --dev   # also build Dev variant
```

Output: `dist/CoPaw.app`, `dist/CoPaw-<version>.dmg`.
With `--dev`: also `dist/CoPaw-Dev.app`, `dist/CoPaw-Dev-<version>.dmg`.

**Release (CoPaw):** Double-click opens a native window with the Console.
**Dev (CoPaw-Dev):** Same UI but opens a **Terminal window** so you can see backend logs and errors.

First launch runs `copaw init --defaults --accept-security` in
`~/Library/Application Support/CoPaw`. Closing the window quits the app and server.

## If macOS says the app is "damaged"

Downloads from the internet are quarantined. If you see "damaged" (common on macOS 15+), remove the quarantine attribute:

```bash
xattr -cr /path/to/CoPaw.app
# or for Dev: xattr -cr /path/to/CoPaw-Dev.app
```

Then open the app again, or in **System Settings → Privacy & Security** allow the app.
