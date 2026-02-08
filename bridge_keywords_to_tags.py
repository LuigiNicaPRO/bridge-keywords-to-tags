#!/usr/bin/env python3
"""
Copy Adobe Bridge Keywords to macOS Finder Tags

This script processes a file or recursively searches a folder for files with Adobe Bridge/XMP keywords
and copies those keywords as Finder tags.

Requirements:
- macOS (for Finder tags)
- exiftool (install via: brew install exiftool)
- fswatch (for watch mode: brew install fswatch)
"""

import subprocess
import json
import os
import sys
import plistlib
import argparse
import time
import signal
from pathlib import Path
from datetime import datetime


# ============================================================================
# WATCH CONFIGURATION - Edit the directories you want to monitor
# ============================================================================
# Add directories to watch (one per line)
# Example:
#   "/Users/yourname/Pictures",
#   "/Users/yourname/Documents/Photos",
#
WATCH_DIRECTORIES = [
    # Add your directories here (uncomment and edit the examples below):
    # "/Users/nica/Pictures",
    "/Users/nica/Downloads/Collection hero 11 front",
    "/Users/nica/Downloads/gw-11-2000",
    # Removed large directories to speed up initial scan:
    # "/Users/nica/Pictures",
    # "/Users/nica/Downloads",
]

# Set to True to replace existing tags, False to merge with existing tags
WATCH_REPLACE_MODE = True  # Replace mode: tags will exactly match keywords

# Strip parent prefixes from hierarchical keywords (e.g., "Other Keywords|hero" -> "hero")
# Set to True to use only the leaf keyword, False to keep the full path
STRIP_HIERARCHICAL_PREFIXES = True

# Marker keyword - only process files with this keyword in their XMP metadata
# Set to None to process all files with keywords, or a string like "sync" to require it
MARKER_KEYWORD = "sync"
# ============================================================================


# File extensions to process (common image/video formats that support XMP)
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp',
    '.psd', '.ai', '.eps', '.pdf',
    '.raw', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.dng',
    '.mov', '.mp4', '.avi', '.mkv',
    '.xmp'  # Sidecar files
}


def check_exiftool():
    """Check if exiftool is installed."""
    try:
        subprocess.run(['exiftool', '-ver'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_xmp_keywords(file_path: Path, strip_prefixes: bool = STRIP_HIERARCHICAL_PREFIXES, debug: bool = False) -> list[str]:
    """Extract XMP keywords from a file using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-json', '-Subject', '-Keywords', '-HierarchicalSubject', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        if debug:
            print(f"  → exiftool stdout: {result.stdout[:300]}...")
        data = json.loads(result.stdout)
        if not data:
            if debug:
                print(f"  → No data returned from exiftool")
            return []
        
        metadata = data[0]
        keywords = set()
        
        # Collect keywords from Keywords and Subject fields only
        # HierarchicalSubject is NOT used because it can contain stale keywords
        # that Adobe Bridge no longer displays (Bridge uses Keywords/Subject)
        for field in ['Subject', 'Keywords']:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, list):
                    for item in value:
                        keywords.add(str(item))
                elif isinstance(value, str):
                    keywords.add(value)
        
        return list(keywords)
    except subprocess.CalledProcessError as e:
        if debug:
            print(f"  → exiftool error (exit {e.returncode}): {e.stderr if e.stderr else 'no stderr'}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        if debug:
            print(f"  → Exception in get_xmp_keywords: {type(e).__name__}: {e}")
        return []


def get_detailed_keywords(file_path: Path) -> dict:
    """Get detailed keyword information from a file including all metadata fields."""
    try:
        result = subprocess.run(
            ['exiftool', '-json', '-Subject', '-Keywords', '-HierarchicalSubject', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        if not data:
            return {}
        
        metadata = data[0]
        return {
            'Keywords': metadata.get('Keywords', []),
            'Subject': metadata.get('Subject', []),
            'HierarchicalSubject': metadata.get('HierarchicalSubject', [])
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return {}


def display_keywords(file_path: Path):
    """Display detailed keyword information for a file."""
    keywords = get_detailed_keywords(file_path)
    
    if not any(keywords.values()):
        print(f"  No keywords found")
        return
    
    for field, values in keywords.items():
        if values:
            if isinstance(values, list):
                # Convert all values to strings to handle mixed types (str and int)
                print(f"  {field:25s}: {', '.join(str(v) for v in values)}")
            else:
                print(f"  {field:25s}: {values}")


def check_keywords_folder(folder_path: Path):
    """Display keywords for all supported files in a folder."""
    file_count = 0
    
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip unsupported file types
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            
            # Skip XMP sidecar files
            if file_path.suffix.lower() == '.xmp':
                continue
            
            file_count += 1
            print(f"\n{file_path}")
            display_keywords(file_path)
    
    return file_count


def get_finder_tags(file_path: Path) -> list[str]:
    """Get existing Finder tags for a file."""
    try:
        result = subprocess.run(
            ['xattr', '-p', 'com.apple.metadata:_kMDItemUserTags', str(file_path)],
            capture_output=True,
            check=True
        )
        # Parse the binary plist data
        plist_data = plistlib.loads(result.stdout)
        # Tags are stored as "TagName\n0" or similar format
        return [tag.split('\n')[0] for tag in plist_data]
    except (subprocess.CalledProcessError, plistlib.InvalidFileException):
        return []


def set_finder_tags(file_path: Path, tags: list[str]) -> bool:
    """Set or clear Finder tags for a file."""
    try:
        if not tags:
            # Clear tags by removing the xattr
            subprocess.run(
                ['xattr', '-d', 'com.apple.metadata:_kMDItemUserTags', str(file_path)],
                capture_output=True,  # Suppress error if attribute doesn't exist
                check=False
            )
            return True
        
        formatted_tags = [f"{tag}\n0" for tag in tags]
        plist_data = plistlib.dumps(formatted_tags, fmt=plistlib.FMT_BINARY)
        
        # Write to temp file and use xattr to read from it
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(plist_data)
            tmp_path = tmp.name
        
        subprocess.run(
            ['xattr', '-wx', 'com.apple.metadata:_kMDItemUserTags', plist_data.hex(), str(file_path)],
            check=True
        )
        os.unlink(tmp_path)
        return True
    except subprocess.CalledProcessError:
        return False


def process_file(file_path: Path, dry_run: bool = False, merge: bool = True, strip_prefixes: bool = STRIP_HIERARCHICAL_PREFIXES, debug: bool = False) -> tuple[bool, list[str]]:
    """
    Process a single file: extract XMP keywords and set as Finder tags.
    
    Returns: (success, keywords_found)
    """
    # Get raw keywords first to check for marker (if needed)
    raw_keywords = get_xmp_keywords(file_path, strip_prefixes=False, debug=debug)
    
    if not raw_keywords:
        if debug:
            print(f"  → No keywords found in file")
        return True, []
    
    # Check for marker keyword if configured
    if MARKER_KEYWORD:
        if debug:
            print(f"  → Checking for marker '{MARKER_KEYWORD}' in: {raw_keywords}")
        if MARKER_KEYWORD not in raw_keywords:
            # No marker keyword found, skip this file
            if debug:
                print(f"  → Marker keyword '{MARKER_KEYWORD}' not found, skipping file")
            return True, []
    
    # Apply prefix stripping if needed
    if strip_prefixes != STRIP_HIERARCHICAL_PREFIXES:
        keywords = get_xmp_keywords(file_path, strip_prefixes=strip_prefixes, debug=debug)
    else:
        keywords = raw_keywords
    
    # Remove marker keyword from the tags to be set
    if MARKER_KEYWORD:
        keywords = [k for k in keywords if k.lower() != MARKER_KEYWORD.lower()]
        if not keywords and merge:
            # In merge mode, skip files with only marker keyword
            if debug:
                print(f"  → No keywords left after removing marker keyword (merge mode, skipping)")
            return True, []
        # In replace mode, continue to clear tags if no keywords left
    
    if merge:
        existing_tags = get_finder_tags(file_path)
        all_tags = list(set(existing_tags + keywords))
    else:
        all_tags = keywords
    
    if dry_run:
        return True, keywords
    
    success = set_finder_tags(file_path, all_tags)
    return success, keywords


def process_xmp_sidecar(sidecar_path: Path, dry_run: bool = False, merge: bool = True, verbose: bool = False, strip_prefixes: bool = STRIP_HIERARCHICAL_PREFIXES) -> tuple[bool, int]:
    """Process an XMP sidecar file and apply keywords to the main file.
    
    Returns: (success, tagged_count)
    """
    main_file = sidecar_path.with_suffix('')
    if not main_file.exists():
        return False, 0
    
    keywords = get_xmp_keywords(sidecar_path, strip_prefixes=strip_prefixes)
    if not keywords:
        return True, 0
    
    # Check for marker keyword if configured
    if MARKER_KEYWORD:
        raw_keywords = get_xmp_keywords(sidecar_path, strip_prefixes=False)
        if MARKER_KEYWORD not in raw_keywords:
            return True, 0
        # Remove marker keyword from tags
        keywords = [k for k in keywords if k.lower() != MARKER_KEYWORD.lower()]
        if not keywords:
            return True, 0
    
    if dry_run:
        return True, 1
    
    if merge:
        existing = get_finder_tags(main_file)
        keywords = list(set(existing + keywords))
    
    success = set_finder_tags(main_file, keywords)
    if verbose and success:
        print(f"  {main_file.name} (from sidecar): {keywords}")
    
    return success, 1 if success else 0


def process_folder(folder_path: Path, dry_run: bool = False, merge: bool = True, verbose: bool = False, strip_prefixes: bool = STRIP_HIERARCHICAL_PREFIXES):
    """Recursively process all supported files in a folder."""
    processed = 0
    tagged = 0
    errors = 0
    
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip unsupported file types
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            
            # Process XMP sidecar files separately
            if file_path.suffix.lower() == '.xmp':
                success, count = process_xmp_sidecar(file_path, dry_run, merge, verbose, strip_prefixes)
                tagged += count
                continue
            
            processed += 1
            success, keywords = process_file(file_path, dry_run, merge, strip_prefixes=strip_prefixes)
            
            if not success:
                errors += 1
                if verbose:
                    print(f"  ERROR: {file_path}")
            elif keywords:
                tagged += 1
                if verbose:
                    print(f"  {file_path.name}: {keywords}")
    
    return processed, tagged, errors


def get_launchd_plist_path() -> Path:
    """Get the path to the launchd plist file."""
    return Path.home() / "Library" / "LaunchAgents" / "com.user.bridge-keywords-watcher.plist"


def get_configured_watch_paths() -> list[Path]:
    """Get the list of directories configured for watching."""
    paths = []
    for path_str in WATCH_DIRECTORIES:
        if path_str and path_str.strip():
            path = Path(path_str).expanduser().resolve()
            if path.exists() and path.is_dir():
                paths.append(path)
            else:
                print(f"Warning: Configured path does not exist or is not a directory: {path_str}")
    return paths


def create_launchd_plist(script_path: Path) -> bool:
    """Create a launchd plist file for the watcher service."""
    plist_path = get_launchd_plist_path()
    
    # Create LaunchAgents directory if it doesn't exist
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build the plist content - uses WATCH_DIRECTORIES from script config
    args = [
        '/usr/bin/python3',
        '-u',  # Unbuffered output for immediate logs
        str(script_path.resolve()),
        '--watch-service'
    ]
    
    # Build args XML (can't use backslash in f-string)
    args_xml = ''.join(f'<string>{arg}</string>\n        ' for arg in args)
    log_dir = Path.home() / "Library" / "Logs"
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.bridge-keywords-watcher</string>
    <key>ProgramArguments</key>
    <array>
        {args_xml}
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_dir}/bridge-keywords-watcher.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/bridge-keywords-watcher-error.log</string>
</dict>
</plist>
'''
    
    try:
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        return True
    except IOError as e:
        print(f"Error creating plist file: {e}")
        return False


def service_status() -> str:
    """Check if the watcher service is running."""
    try:
        result = subprocess.run(
            ['launchctl', 'list'],
            capture_output=True,
            text=True,
            check=False,
            timeout=2
        )
        if 'com.user.bridge-keywords-watcher' in result.stdout:
            return 'running'
        else:
            plist_path = get_launchd_plist_path()
            if plist_path.exists():
                return 'stopped'
            else:
                return 'not-installed'
    except Exception:
        return 'unknown'


def service_install(script_path: Path, autostart: bool = False) -> bool:
    """Install the watcher service."""
    plist_path = get_launchd_plist_path()
    
    # Check if already installed
    if plist_path.exists():
        print("Service is already installed.")
        print("Use 'service-uninstall' first if you want to reinstall.")
        return False
    
    # Check if there are any watch paths configured
    watch_paths = get_configured_watch_paths()
    if not watch_paths:
        print("Error: No directories are configured for watching.")
        print(f"Edit the WATCH_DIRECTORIES section in {script_path} to add directories.")
        return False
    
    # Create the plist file
    if not create_launchd_plist(script_path):
        return False
    
    # If autostart is enabled, modify the plist to set RunAtLoad to true
    if autostart:
        try:
            with open(plist_path, 'r') as f:
                content = f.read()
            content = content.replace('<key>RunAtLoad</key>\n    <false/>', 
                                     '<key>RunAtLoad</key>\n    <true/>')
            with open(plist_path, 'w') as f:
                f.write(content)
        except IOError as e:
            print(f"Warning: Could not enable autostart: {e}")
    
    print(f"✓ Service installed successfully")
    print(f"  Watching {len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}:")
    for path in watch_paths:
        print(f"    - {path}")
    print(f"  Autostart on login: {'enabled' if autostart else 'disabled'}")
    print(f"  Log file: {Path.home()}/Library/Logs/bridge-keywords-watcher.log")
    print("\nUse 'service-start' to start the service now.")
    print(f"To add/remove directories, edit WATCH_DIRECTORIES in {script_path}")
    return True


def service_uninstall() -> bool:
    """Uninstall the watcher service."""
    plist_path = get_launchd_plist_path()
    
    if not plist_path.exists():
        print("Service is not installed.")
        return False
    
    # Stop the service if it's running
    status = service_status()
    if status == 'running':
        print("Stopping service first...")
        service_stop()
    
    # Remove the plist file
    try:
        plist_path.unlink()
        print("✓ Service uninstalled successfully")
        return True
    except OSError as e:
        print(f"Error uninstalling service: {e}")
        return False


def service_start() -> bool:
    """Start the watcher service."""
    plist_path = get_launchd_plist_path()
    
    if not plist_path.exists():
        print("Service is not installed. Use 'service-install' first.")
        return False
    
    status = service_status()
    if status == 'running':
        print("Service is already running.")
        return True
    
    try:
        subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
        print("✓ Service started successfully")
        print(f"  Log file: {Path.home()}/Library/Logs/bridge-keywords-watcher.log")
        print("\nUse 'service-status' to check the service status.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting service: {e}")
        return False


def service_stop() -> bool:
    """Stop the watcher service."""
    plist_path = get_launchd_plist_path()
    
    if not plist_path.exists():
        print("Service is not installed.")
        return False
    
    status = service_status()
    if status == 'stopped':
        print("Service is not running.")
        return True
    
    try:
        subprocess.run(['launchctl', 'unload', str(plist_path)], check=True)
        print("✓ Service stopped successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping service: {e}")
        return False


def service_restart() -> bool:
    """Restart the watcher service."""
    plist_path = get_launchd_plist_path()
    
    if not plist_path.exists():
        print("Service is not installed.")
        return False
    
    print("Stopping service...")
    # Force unload, ignoring errors (service might be in failed state)
    subprocess.run(['launchctl', 'unload', str(plist_path)], 
                   capture_output=True, check=False)
    time.sleep(1)
    print("Starting service...")
    return service_start()


def service_logs(follow: bool = False):
    """Display service logs."""
    log_path = Path.home() / "Library" / "Logs" / "bridge-keywords-watcher.log"
    error_log_path = Path.home() / "Library" / "Logs" / "bridge-keywords-watcher-error.log"
    
    if not log_path.exists() and not error_log_path.exists():
        print("No log files found. The service may not have been started yet.")
        return
    
    if follow:
        print("Following logs (press Ctrl+C to stop)...\n")
        try:
            subprocess.run(['tail', '-f', str(log_path)], check=False)
        except KeyboardInterrupt:
            print("\nStopped following logs.")
    else:
        if log_path.exists():
            print("=== Output Log ===")
            with open(log_path, 'r') as f:
                print(f.read())
        
        if error_log_path.exists():
            print("\n=== Error Log ===")
            with open(error_log_path, 'r') as f:
                content = f.read()
                if content.strip():
                    print(content)
                else:
                    print("(empty)")


def watch_directories(watch_paths: list[Path], merge: bool = True, verbose: bool = False, from_service: bool = False, strip_prefixes: bool = STRIP_HIERARCHICAL_PREFIXES):
    """Watch directories for file changes and automatically sync keywords to tags."""
    if not from_service:
        print("Starting file watcher...")
        print(f"Watching {len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}:")
        for path in watch_paths:
            print(f"  - {path}")
        print(f"Strip hierarchical prefixes: {'enabled' if strip_prefixes else 'disabled'}")
        print("\nPress Ctrl+C to stop\n")
    else:
        # Service mode - log startup
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Service started")
        print(f"Watching {len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}:")
        for path in watch_paths:
            print(f"  - {path}")
        print(f"Strip hierarchical prefixes: {'enabled' if strip_prefixes else 'disabled'}")
    
    # Track last modification times to avoid duplicate processing
    last_processed = {}
    
    # Batch processing: collect files for 1 second before processing
    pending_files = set()
    last_event_time = None
    
    # Initial scan of all directories
    print("Performing initial scan...")
    for watch_path in watch_paths:
        if watch_path.is_dir():
            processed, tagged, errors = process_folder(watch_path, dry_run=False, merge=merge, verbose=verbose, strip_prefixes=strip_prefixes)
            if verbose:
                print(f"Initial scan of {watch_path}: {tagged} files tagged")
    
    print("\nWatching for changes...\n")
    
    # Use fswatch to monitor directories
    # fswatch is more reliable than Python's watchdog on macOS
    # Check for fswatch in common locations
    fswatch_path = None
    for path in ['/opt/homebrew/bin/fswatch', '/usr/local/bin/fswatch', '/usr/bin/fswatch']:
        if Path(path).exists():
            fswatch_path = path
            break
    
    if not fswatch_path:
        print("Error: fswatch is not installed.")
        print("Install it with: brew install fswatch")
        sys.exit(1)
    
    # Build fswatch command
    # Watch for Updated (content changes), Created (new files), and AttributeModified (XMP metadata changes)
    fswatch_cmd = [fswatch_path, '-r', '--event', 'Updated', '--event', 'Created', '--event', 'AttributeModified'] + [str(p) for p in watch_paths]
    
    try:
        process = subprocess.Popen(
            fswatch_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0  # Unbuffered for immediate output
        )
        
        # Process file changes as they're detected
        # Use a non-blocking approach with select to batch events
        import select
        
        while True:
            # Check if data is available (with 2 second timeout for batching)
            ready, _, _ = select.select([process.stdout], [], [], 2)
            
            if ready:
                # Read available line
                line = process.stdout.readline()
                if not line:
                    break  # Process ended
                    
                changed_path = Path(line.strip())
                
                # Skip if not a supported file
                if changed_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                
                # Skip if file doesn't exist
                if not changed_path.exists():
                    continue
                
                # Check modification time to avoid duplicate processing
                try:
                    mtime = changed_path.stat().st_mtime
                    last_mtime = last_processed.get(changed_path, 0)
                    
                    # Skip if same modification time (duplicate event)
                    if last_mtime > 0 and mtime == last_mtime:
                        continue
                    
                    last_processed[changed_path] = mtime
                except OSError:
                    continue
                
                # Add to batch
                pending_files.add(changed_path)
                last_event_time = time.time()
                
            else:
                # Timeout - no new events for 2 seconds
                if pending_files and last_event_time:
                    # Check if 1 second has passed since last event
                    if time.time() - last_event_time >= 1:
                        # Process all pending files
                        if from_service:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"[{timestamp}] Processing {len(pending_files)} file(s)...")
                        
                        # Build command to process all files
                        script_path = Path(__file__).resolve()
                        files_to_process = list(pending_files)
                        
                        for file_path in files_to_process:
                            try:
                                # Build command with replace flag if needed
                                cmd = ['python3', str(script_path), str(file_path), '-v']
                                if not merge:  # merge=False means replace mode
                                    cmd.append('-r')
                                
                                result = subprocess.run(
                                    cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                if from_service:
                                    if result.returncode == 0 and 'Files with keywords: 1' in result.stdout:
                                        print(f"  ✓ Synced: {file_path.name}")
                                    elif result.returncode != 0:
                                        print(f"  ✗ ERROR: {file_path.name}")
                            except Exception as e:
                                if from_service:
                                    print(f"  ✗ {file_path.name}: {str(e)[:100]}")
                        
                        # Clear batch
                        pending_files.clear()
                        last_event_time = None
    
    except KeyboardInterrupt:
        print("\n\nStopping file watcher...")
        process.terminate()
        process.wait()
        print("Watcher stopped.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Copy Adobe Bridge keywords to macOS Finder tags',
        epilog='Service commands: service-install, service-uninstall, service-start, service-stop, service-restart, service-status, service-logs'
    )
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        help='File or folder to process (not required for service commands)'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '-r', '--replace',
        action='store_true',
        help='Replace existing tags instead of merging'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output for each file'
    )
    parser.add_argument(
        '-c', '--check',
        action='store_true',
        help='Display keywords in files without applying tags'
    )
    parser.add_argument(
        '-w', '--watch',
        action='store_true',
        help='Watch directory for changes and automatically sync keywords to tags'
    )
    parser.add_argument(
        '--watch-service',
        action='store_true',
        help=argparse.SUPPRESS  # Hidden flag used by the launchd service
    )
    parser.add_argument(
        '--autostart',
        action='store_true',
        help='(For service-install) Enable service to start automatically on login'
    )
    parser.add_argument(
        '--follow',
        action='store_true',
        help='(For service-logs) Follow log output in real-time'
    )
    parser.add_argument(
        '--keep-prefixes',
        action='store_true',
        help='Keep hierarchical keyword prefixes (e.g., "Category|Keyword" instead of just "Keyword")'
    )
    
    args = parser.parse_args()
    
    # Handle --watch-service (used by launchd, reads from WATCH_DIRECTORIES config)
    if args.watch_service:
        watch_paths = get_configured_watch_paths()
        if not watch_paths:
            print("Error: No valid directories configured in WATCH_DIRECTORIES")
            sys.exit(1)
        watch_directories(watch_paths, merge=not WATCH_REPLACE_MODE, verbose=False, from_service=True)
        sys.exit(0)
    
    # Handle service commands
    if args.path in ['service-install', 'service-uninstall', 'service-start', 
                     'service-stop', 'service-restart', 'service-status', 'service-logs']:
        command = args.path
        
        if command == 'service-status':
            status = service_status()
            plist_path = get_launchd_plist_path()
            watch_paths = get_configured_watch_paths()
            
            print(f"Service status: {status}")
            if status != 'not-installed':
                print(f"Config file: {plist_path}")
                if status == 'running':
                    print(f"Log file: {Path.home()}/Library/Logs/bridge-keywords-watcher.log")
            
            if watch_paths:
                print(f"\nConfigured to watch {len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}:")
                for path in watch_paths:
                    print(f"  - {path}")
            else:
                print("\nNo directories configured in WATCH_DIRECTORIES")
            
            if status == 'not-installed':
                print("\nInstall the service with: python3 bridge_keywords_to_tags.py service-install")
            elif status == 'stopped':
                print("\nStart the service with: python3 bridge_keywords_to_tags.py service-start")
            sys.exit(0)
            
        elif command == 'service-install':
            script_path = Path(__file__)
            service_install(script_path, autostart=args.autostart)
            sys.exit(0)
            
        elif command == 'service-uninstall':
            service_uninstall()
            sys.exit(0)
            
        elif command == 'service-start':
            service_start()
            sys.exit(0)
            
        elif command == 'service-stop':
            service_stop()
            sys.exit(0)
            
        elif command == 'service-restart':
            service_restart()
            sys.exit(0)
            
        elif command == 'service-logs':
            service_logs(follow=args.follow)
            sys.exit(0)
    
    # Validate that path is provided for non-service commands
    if not args.path:
        print("Error: path argument is required")
        print("\nService commands:")
        print("  service-install <directory> [--autostart] - Install background service")
        print("  service-start                            - Start the service")
        print("  service-stop                             - Stop the service")
        print("  service-restart                          - Restart the service")
        print("  service-status                           - Check service status")
        print("  service-uninstall                        - Uninstall the service")
        print("  service-logs [--follow]                  - View service logs")
        sys.exit(1)
    
    path = Path(args.path).expanduser().resolve()
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        sys.exit(1)
    
    if not check_exiftool():
        print("Error: exiftool is not installed.")
        print("Install it with: brew install exiftool")
        sys.exit(1)
    
    # Handle check mode (display keywords only)
    if args.check:
        print(f"Checking keywords in: {path}")
        print("=" * 70)
        
        if path.is_dir():
            file_count = check_keywords_folder(path)
            print("\n" + "=" * 70)
            print(f"Files checked: {file_count}")
        else:
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                print(f"Error: File extension '{path.suffix}' is not supported")
                sys.exit(1)
            
            print(f"\n{path}")
            display_keywords(path)
            print("\n" + "=" * 70)
        
        sys.exit(0)
    
    # Handle watch mode
    if args.watch:
        if not path.is_dir():
            print("Error: Watch mode requires a directory path, not a file.")
            sys.exit(1)
        
        strip_prefixes = not args.keep_prefixes if hasattr(args, 'keep_prefixes') else STRIP_HIERARCHICAL_PREFIXES
        watch_directories([path], merge=not args.replace, verbose=args.verbose, strip_prefixes=strip_prefixes)
        sys.exit(0)
    
    if args.dry_run:
        print(f"DRY RUN - No changes will be made\n")
    
    print(f"Processing: {path}")
    print("-" * 50)
    
    strip_prefixes = not args.keep_prefixes if hasattr(args, 'keep_prefixes') else STRIP_HIERARCHICAL_PREFIXES
    
    if path.is_dir():
        processed, tagged, errors = process_folder(
            path,
            dry_run=args.dry_run,
            merge=not args.replace,
            verbose=args.verbose,
            strip_prefixes=strip_prefixes
        )
    else:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"Error: File extension '{path.suffix}' is not supported")
            sys.exit(1)
        
        processed = 1
        success, keywords = process_file(path, dry_run=args.dry_run, merge=not args.replace, strip_prefixes=strip_prefixes)
        tagged = 1 if keywords else 0
        errors = 0 if success else 1
        
        if not success:
            if args.verbose:
                print(f"  ERROR: {path}")
        elif keywords:
            if args.verbose:
                print(f"  {path.name}: {keywords}")
    
    print("-" * 50)
    print(f"Files scanned: {processed}")
    print(f"Files with keywords: {tagged}")
    if errors:
        print(f"Errors: {errors}")
    
    if args.dry_run:
        print("\nRun without --dry-run to apply changes")


if __name__ == '__main__':
    main()
