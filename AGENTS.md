# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Bridge Keywords to Tags** is a macOS application that synchronizes Adobe Bridge/XMP keywords from image files to macOS Finder tags. The project consists of three integrated Python applications packaged as a native macOS app bundle.

### Core Architecture

The system has three main components that work together:

1. **Core Engine** (`bridge_keywords_to_tags.py`)
   - Reads XMP metadata using `exiftool`
   - Writes Finder tags using `xattr` and binary plist encoding
   - Handles background service via launchd
   - Manages file system watching with `fswatch`
   - Configuration stored as Python constants at top of file

2. **Menu Bar App** (`bridge_menubar.py`)
   - Uses `rumps` framework for menu bar integration
   - Imports core engine as module: `import bridge_keywords_to_tags as bkt`
   - All operations run in background threads to prevent UI blocking
   - Singleton instance enforced via file locking (`/tmp/bridge_menubar.lock`)

3. **GUI Dashboard** (`bridge_dashboard_gui.py`)
   - Built with tkinter (standard library)
   - Also imports core engine: `import bridge_keywords_to_tags as bkt`
   - Directory management writes directly to config file then reloads module
   - All service operations run asynchronously via threading

### Critical Design Patterns

**Module Import Pattern**: Menu bar and dashboard don't shell out to the core script - they import it as a module and call its functions directly. This means configuration changes require module reloading:

```python
import importlib
importlib.reload(bkt)
```

**Threading for UI**: Both GUI applications use threading to prevent blocking:
- Menu bar: Each callback spawns a daemon thread
- Dashboard: Service operations run in background threads with `root.after()` for UI updates

**Configuration Management**: 
- Config lives at top of `bridge_keywords_to_tags.py` as module-level constants
- `WATCH_DIRECTORIES` is a Python list (not a separate config file)
- Dashboard edits config by reading/writing Python source file directly
- launchd plist reads these values at service start via `--watch-service` flag

**Binary Plist Encoding for Tags**:
```python
formatted_tags = [f"{tag}\n0" for tag in tags]
plist_data = plistlib.dumps(formatted_tags, fmt=plistlib.FMT_BINARY)
subprocess.run(['xattr', '-wx', 'com.apple.metadata:_kMDItemUserTags', plist_data.hex(), ...])
```

## Development Commands

### Testing the Core Engine

```bash
# Check what keywords are in a file
python3 bridge_keywords_to_tags.py "photo.jpg" --check

# Dry run on a directory (see what would happen)
python3 bridge_keywords_to_tags.py ~/Pictures -n -v

# Process a single file with verbose output
python3 bridge_keywords_to_tags.py "photo.jpg" -v

# Process directory (merge mode - preserves existing tags)
python3 bridge_keywords_to_tags.py ~/Pictures -v

# Replace existing tags instead of merging
python3 bridge_keywords_to_tags.py ~/Pictures -r -v
```

### Service Management

```bash
# Check service status and configuration
python3 bridge_keywords_to_tags.py service-status

# Install service (doesn't auto-start on login)
python3 bridge_keywords_to_tags.py service-install

# Install with auto-start at login
python3 bridge_keywords_to_tags.py service-install --autostart

# Start/stop/restart
python3 bridge_keywords_to_tags.py service-start
python3 bridge_keywords_to_tags.py service-stop
python3 bridge_keywords_to_tags.py service-restart

# View logs
python3 bridge_keywords_to_tags.py service-logs
python3 bridge_keywords_to_tags.py service-logs --follow

# Uninstall
python3 bridge_keywords_to_tags.py service-uninstall
```

### Running the GUI Applications

```bash
# Menu bar app (runs until quit)
python3 bridge_menubar.py

# Dashboard (opens window)
python3 bridge_dashboard_gui.py

# Launch from app bundle
open "Bridge Keywords to Tags.app"
```

### Testing Watch Mode

```bash
# Watch a directory for changes (Ctrl+C to stop)
python3 bridge_keywords_to_tags.py ~/Pictures --watch -v

# Watch with replace mode instead of merge
python3 bridge_keywords_to_tags.py ~/Pictures --watch -r
```

## Configuration Details

### Location
All configuration is in `bridge_keywords_to_tags.py` at lines 27-53 (the `WATCH CONFIGURATION` section).

### Key Settings

```python
WATCH_DIRECTORIES = [
    "/Users/nica/Downloads/Collection hero 11 front",
    "/Users/nica/Downloads/gw-11-2000",
    "/Users/nica/Pictures",
    "/Users/nica/Downloads",
]

WATCH_REPLACE_MODE = False  # False = merge, True = replace
STRIP_HIERARCHICAL_PREFIXES = True  # "Other Keywords|hero" → "hero"
MARKER_KEYWORD = "sync"  # Only process files with this keyword, or None for all
```

### Changing Configuration

**Via GUI Dashboard**: Use the "+" button in Watched Directories section. Changes are written to the Python file and module is reloaded.

**Manually**: Edit the constants in `bridge_keywords_to_tags.py`, then restart the service:
```bash
python3 bridge_keywords_to_tags.py service-restart
```

**For marker keyword**: Use menu bar app → click "sync enabled" / "all enabled" to toggle between modes.

## File Locations

### Application Files
- App bundle: `/Users/nica/python-scripts/Bridge Keywords Sync/Bridge Keywords to Tags.app`
- Scripts are in: `Bridge Keywords to Tags.app/Contents/Resources/`
- Development copies also exist in project root (same directory)

### Runtime Files
- Service plist: `~/Library/LaunchAgents/com.user.bridge-keywords-watcher.plist`
- Menu bar plist: `~/Library/LaunchAgents/com.user.bridge-menubar.plist`
- Service logs: `~/Library/Logs/bridge-keywords-watcher.log`
- Lock file: `/tmp/bridge_menubar.lock`

## Debugging Common Issues

### "Module not found" errors
The menu bar and dashboard import the core script. Ensure they're in the same directory:
```bash
ls -l bridge_*.py
```

### Service won't start
Check the plist exists and directories are configured:
```bash
python3 bridge_keywords_to_tags.py service-status
cat ~/Library/LaunchAgents/com.user.bridge-keywords-watcher.plist
```

View error logs:
```bash
tail -f ~/Library/Logs/bridge-keywords-watcher-error.log
```

### Dashboard folder picker not working
The AppleScript folder picker returns POSIX paths directly. If broken, check this in dashboard code:
```python
applescript = '''
tell application "Finder"
    POSIX path of (choose folder with prompt "Select directory to watch:")
end tell
'''
```

### Service restart errors
The restart command uses `check=False` on unload to handle failed states:
```python
subprocess.run(['launchctl', 'unload', str(plist_path)], capture_output=True, check=False)
```

### Window focus issues (Dashboard)
Window should auto-focus after folder selection via:
```python
self.root.lift()
self.root.focus_force()
```

## Dependencies

### System Requirements
- macOS (uses Finder tags, launchd, xattr, FSEvents)
- Python 3 (tested with `/opt/anaconda3/bin/python3`)

### External Tools (via Homebrew)
```bash
brew install exiftool fswatch
```

### Python Packages
```bash
pip3 install rumps  # For menu bar app only
# tkinter included with Python
```

## Adding New Features

### Adding a new file format
Edit `SUPPORTED_EXTENSIONS` in `bridge_keywords_to_tags.py`:
```python
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', # ... existing
    '.heic',  # Add new format
}
```

### Adding a new menu item
In `bridge_menubar.py`, add to the menu list in `__init__`:
```python
self.menu = [
    rumps.MenuItem("New Feature", callback=self.new_feature),
    # ...
]
```

Then implement the callback with async pattern:
```python
@rumps.clicked("New Feature")
def new_feature(self, _):
    def feature_async():
        try:
            # Do work here
            rumps.notification(title="Success", subtitle="", message="Done")
        except Exception as e:
            rumps.notification(title="Error", subtitle="", message=str(e))
    
    threading.Thread(target=feature_async, daemon=True).start()
```

### Adding dashboard controls
Add widgets in `bridge_dashboard_gui.py` `__init__`:
```python
new_btn = ttk.Button(button_frame, text="New Feature", 
                     command=self.new_feature, width=15)
new_btn.grid(row=0, column=4, padx=5)
```

Implement with threading pattern:
```python
def new_feature(self):
    def thread_func():
        try:
            # Do work
            self.root.after(0, lambda: self.status_bar.config(text="Success"))
        except Exception as e:
            self.root.after(0, lambda: self.status_bar.config(text=f"Error: {e}"))
    
    threading.Thread(target=thread_func, daemon=True).start()
```

## Important Implementation Notes

### Never Block the UI Thread
Both GUI apps must use threading for any operation that:
- Calls subprocess
- Reads files
- Interacts with launchd
- Processes images

### Preserve Module Import Pattern
When adding features that need config values, import and use the module:
```python
import bridge_keywords_to_tags as bkt
# Then access: bkt.WATCH_DIRECTORIES, bkt.MARKER_KEYWORD, etc.
```

### Handle launchd State Carefully
Services can be in failed state. Always use `check=False` for unload operations in restart:
```python
subprocess.run(['launchctl', 'unload', plist], check=False)
```

### Finder Tag Format is Strict
Tags must be formatted as `"{tag_name}\n0"` in a binary plist, then hex-encoded for xattr.

### fswatch Path Resolution
Check multiple paths since fswatch location varies by Homebrew version:
```python
for path in ['/opt/homebrew/bin/fswatch', '/usr/local/bin/fswatch', '/usr/bin/fswatch']:
    if Path(path).exists():
        fswatch_path = path
        break
```

## Testing Workflow

1. Test core functionality first:
```bash
python3 bridge_keywords_to_tags.py "test_photo.jpg" -n -v
```

2. Test service management:
```bash
python3 bridge_keywords_to_tags.py service-install
python3 bridge_keywords_to_tags.py service-start
python3 bridge_keywords_to_tags.py service-status
```

3. Test GUI applications:
```bash
python3 bridge_menubar.py &
python3 bridge_dashboard_gui.py
```

4. Test app bundle:
```bash
open "Bridge Keywords to Tags.app"
```

## Version Control

This repository is tracked with git. Current branch is `main`. When making changes:

```bash
# Check status
git status

# Stage changes
git add bridge_keywords_to_tags.py

# Commit with descriptive message
git commit -m "Add support for HEIC files"

# Push to GitHub
git push
```

**Important**: Do NOT add "Co-Authored-By: Warp <agent@warp.dev>" to commit messages.

Repository: https://github.com/LuigiNicaPRO/bridge-keywords-to-tags
