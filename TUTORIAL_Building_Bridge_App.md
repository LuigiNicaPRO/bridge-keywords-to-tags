# Tutorial: Building a Keyword Sync Application for macOS

This tutorial teaches you how to build the **Bridge Keywords to Tags** application from scratch. You'll learn Python programming, macOS integration, file system operations, and how to create a complete application with multiple interfaces.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Core Functionality](#part-1-core-functionality)
4. [Part 2: Command-Line Interface](#part-2-command-line-interface)
5. [Part 3: Background Service](#part-3-background-service)
6. [Part 4: Menu Bar Application](#part-4-menu-bar-application)
7. [Part 5: GUI Dashboard](#part-5-gui-dashboard)
8. [Part 6: App Bundle](#part-6-app-bundle)
9. [Testing and Debugging](#testing-and-debugging)
10. [Next Steps](#next-steps)

---

## Project Overview

### What We're Building

A system that automatically synchronizes keywords from Adobe Bridge (stored in XMP metadata) to macOS Finder tags, making your photo library searchable through Spotlight and Finder.

### Components

1. **Core Engine** - Reads XMP keywords, writes Finder tags
2. **CLI Tool** - Process files/folders on demand
3. **Background Service** - Watches folders for changes
4. **Menu Bar App** - Control center in the menu bar
5. **GUI Dashboard** - Visual management interface
6. **App Bundle** - Native macOS application

### Technologies Used

- **Python 3** - Main programming language
- **exiftool** - Read XMP metadata from images
- **fswatch** - Monitor file system for changes
- **launchd** - macOS background service system
- **rumps** - Menu bar integration
- **tkinter** - GUI framework
- **xattr** - macOS extended attributes for tags

### Architecture

```
┌─────────────────────────────────────────────┐
│         Bridge Keywords to Tags.app         │
│  ┌─────────────┐         ┌───────────────┐ │
│  │  Menu Bar   │◄───────►│  GUI Dashboard│ │
│  │     App     │         │               │ │
│  └──────┬──────┘         └───────┬───────┘ │
│         │                         │         │
│         └──────────┬──────────────┘         │
│                    ▼                        │
│         ┌──────────────────────┐           │
│         │   Core Engine        │           │
│         │ bridge_keywords_to_  │           │
│         │      tags.py         │           │
│         └──────────────────────┘           │
│                    │                        │
└────────────────────┼────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    exiftool    fswatch      launchd
```

---

## Prerequisites

### Required Knowledge

**Basic Level:**
- Python basics (variables, functions, loops)
- Command line usage (cd, ls, running scripts)
- File system concepts (directories, paths)

**Intermediate Level:**
- Python modules and imports
- Reading/writing files
- Error handling (try/except)

**Advanced Level (for later parts):**
- Threading
- GUI programming
- Shell scripting

**Don't worry if you don't know everything!** This tutorial explains concepts as we go.

### Required Software

```bash
# Check if you have Python 3
python3 --version

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install exiftool fswatch

# Install Python package
pip3 install rumps --user
```

### Understanding the Problem

**The Problem:**
- Adobe Bridge stores keywords in XMP metadata inside image files
- macOS can't read XMP metadata for search
- You want to find images using Finder and Spotlight

**The Solution:**
- Read keywords from XMP using exiftool
- Write them as Finder tags using xattr
- Tags are searchable by Spotlight

---

## Part 1: Core Functionality

Let's build the heart of the application: reading keywords and writing tags.

### Step 1: Understanding XMP Keywords

XMP (Extensible Metadata Platform) is Adobe's standard for storing metadata in files.

**View XMP data in a file:**
```bash
exiftool -Keywords -Subject -HierarchicalSubject photo.jpg
```

**Example output:**
```
Keywords                        : hero, collection, front
Subject                         : hero, collection, front
Hierarchical Subject            : Other Keywords|hero
```

**Three fields store keywords:**
1. `Keywords` - Flat keyword list
2. `Subject` - Same as Keywords (different software uses different names)
3. `HierarchicalSubject` - Nested keywords like `Category|Subcategory|Item`

### Step 2: Reading Keywords with Python

Create a new file: `keyword_reader.py`

```python
#!/usr/bin/env python3
"""
Step 1: Read keywords from an image file
"""
import subprocess
import json
from pathlib import Path


def get_xmp_keywords(file_path):
    """
    Extract keywords from a file using exiftool.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        List of keywords found in the file
    """
    # Convert to Path object for easier handling
    file_path = Path(file_path)
    
    # Run exiftool and capture output
    result = subprocess.run(
        [
            'exiftool',
            '-json',  # Output as JSON for easy parsing
            '-Subject',
            '-Keywords', 
            '-HierarchicalSubject',
            str(file_path)
        ],
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Return strings, not bytes
        check=True           # Raise exception if command fails
    )
    
    # Parse JSON output
    data = json.loads(result.stdout)
    
    # exiftool returns a list with one dict per file
    if not data:
        return []
    
    metadata = data[0]
    keywords = set()  # Use set to avoid duplicates
    
    # Collect keywords from all three fields
    for field in ['Subject', 'Keywords', 'HierarchicalSubject']:
        if field in metadata:
            value = metadata[field]
            
            # Value might be a string or a list
            if isinstance(value, list):
                for item in value:
                    keywords.add(str(item))
            elif isinstance(value, str):
                keywords.add(value)
    
    return list(keywords)


# Test it out
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 keyword_reader.py photo.jpg")
        sys.exit(1)
    
    file_path = sys.argv[1]
    keywords = get_xmp_keywords(file_path)
    
    print(f"Found {len(keywords)} keywords:")
    for keyword in keywords:
        print(f"  - {keyword}")
```

**Understanding the code:**

```python
subprocess.run([...], capture_output=True, text=True, check=True)
```
- `subprocess.run()` - Runs external commands (like exiftool)
- `capture_output=True` - Save command output
- `text=True` - Get output as string (not bytes)
- `check=True` - Raise exception if command fails

```python
keywords = set()
```
- `set()` - Collection that automatically removes duplicates
- Keywords might appear in multiple fields (Subject AND Keywords)

```python
if isinstance(value, list):
```
- Check if value is a list or string
- exiftool returns different formats depending on how many items exist

**Test it:**
```bash
python3 keyword_reader.py photo.jpg
```

### Step 3: Understanding macOS Finder Tags

Finder tags are stored in extended attributes (xattr).

**View tags on a file:**
```bash
xattr -p com.apple.metadata:_kMDItemUserTags photo.jpg | xxd
```

Tags are stored as a binary plist (property list) with this format:
```
["tag1\n0", "tag2\n0", "tag3\n0"]
```

Each tag is followed by `\n` (newline) and a color code (0 = no color).

### Step 4: Writing Finder Tags with Python

Add to `keyword_reader.py`:

```python
import plistlib


def set_finder_tags(file_path, tags):
    """
    Set Finder tags for a file.
    
    Args:
        file_path: Path to the file
        tags: List of tag names to apply
        
    Returns:
        True if successful, False otherwise
    """
    if not tags:
        return True
    
    file_path = Path(file_path)
    
    # Format: ["tag1\n0", "tag2\n0", ...]
    # The \n0 means "no color"
    formatted_tags = [f"{tag}\n0" for tag in tags]
    
    # Convert to binary plist format
    plist_data = plistlib.dumps(
        formatted_tags, 
        fmt=plistlib.FMT_BINARY
    )
    
    try:
        # Write to extended attribute
        subprocess.run(
            [
                'xattr',
                '-wx',  # Write hex data
                'com.apple.metadata:_kMDItemUserTags',
                plist_data.hex(),  # Convert bytes to hex string
                str(file_path)
            ],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_finder_tags(file_path):
    """
    Get existing Finder tags from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of tag names currently on the file
    """
    file_path = Path(file_path)
    
    try:
        result = subprocess.run(
            [
                'xattr',
                '-p',
                'com.apple.metadata:_kMDItemUserTags',
                str(file_path)
            ],
            capture_output=True,
            check=True
        )
        
        # Parse binary plist
        plist_data = plistlib.loads(result.stdout)
        
        # Strip the \n0 suffix from each tag
        tags = [tag.split('\n')[0] for tag in plist_data]
        return tags
        
    except subprocess.CalledProcessError:
        # File has no tags
        return []
```

**Understanding plist:**

```python
plistlib.dumps(formatted_tags, fmt=plistlib.FMT_BINARY)
```
- `dumps()` - Convert Python data to plist format
- `FMT_BINARY` - Use binary format (required by macOS)
- Returns bytes

```python
plist_data.hex()
```
- Convert bytes to hexadecimal string
- xattr expects hex when using `-wx` flag

### Step 5: Combining Read and Write

Add the main processing function:

```python
def process_file(file_path, merge=True):
    """
    Process a file: read keywords and write as tags.
    
    Args:
        file_path: Path to the image file
        merge: If True, add to existing tags. If False, replace them.
        
    Returns:
        Tuple of (success, keywords_found)
    """
    file_path = Path(file_path)
    
    # Get keywords from XMP metadata
    keywords = get_xmp_keywords(file_path)
    
    if not keywords:
        print(f"No keywords found in {file_path.name}")
        return True, []
    
    # Decide whether to merge or replace
    if merge:
        # Get existing tags
        existing_tags = get_finder_tags(file_path)
        
        # Combine (set removes duplicates)
        all_tags = list(set(existing_tags + keywords))
    else:
        all_tags = keywords
    
    # Write tags
    success = set_finder_tags(file_path, all_tags)
    
    if success:
        print(f"✓ {file_path.name}: Applied {len(keywords)} keywords")
    else:
        print(f"✗ {file_path.name}: Failed to set tags")
    
    return success, keywords


# Update the test section
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 keyword_reader.py photo.jpg")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("Reading keywords...")
    keywords = get_xmp_keywords(file_path)
    print(f"Found: {', '.join(keywords)}")
    
    print("\nProcessing file...")
    success, _ = process_file(file_path)
    
    if success:
        print("\n✓ Tags applied successfully!")
        print("Check in Finder: press Cmd+I to see tags")
```

**Test the complete flow:**
```bash
python3 keyword_reader.py photo.jpg
```

**Verify it worked:**
1. Open Finder
2. Find the photo
3. Press Cmd+I (Get Info)
4. Check the Tags section

### Step 6: Handling Hierarchical Keywords

Hierarchical keywords look like `Category|Subcategory|Item`. Often we only want the last part (`Item`).

Add this function:

```python
def strip_hierarchical_prefix(keyword):
    """
    Strip parent categories from hierarchical keywords.
    
    Example: "Other Keywords|hero" -> "hero"
    
    Args:
        keyword: Keyword string (might contain | separator)
        
    Returns:
        The leaf keyword (last part after |)
    """
    if '|' in keyword:
        return keyword.split('|')[-1]
    return keyword


def get_xmp_keywords(file_path, strip_prefixes=True):
    """
    Extract keywords from a file using exiftool.
    
    Args:
        file_path: Path to the image file
        strip_prefixes: If True, strip hierarchical prefixes
        
    Returns:
        List of keywords found in the file
    """
    file_path = Path(file_path)
    
    result = subprocess.run(
        ['exiftool', '-json', '-Subject', '-Keywords', 
         '-HierarchicalSubject', str(file_path)],
        capture_output=True,
        text=True,
        check=True
    )
    
    data = json.loads(result.stdout)
    if not data:
        return []
    
    metadata = data[0]
    keywords = set()
    
    for field in ['Subject', 'Keywords', 'HierarchicalSubject']:
        if field in metadata:
            value = metadata[field]
            
            if isinstance(value, list):
                for item in value:
                    item_str = str(item)
                    
                    # Strip prefix for hierarchical field
                    if strip_prefixes and field == 'HierarchicalSubject':
                        item_str = strip_hierarchical_prefix(item_str)
                    
                    keywords.add(item_str)
                    
            elif isinstance(value, str):
                if strip_prefixes and field == 'HierarchicalSubject':
                    value = strip_hierarchical_prefix(value)
                keywords.add(value)
    
    return list(keywords)
```

**Why strip prefixes?**

Adobe Bridge uses hierarchical keywords for organization:
- `People|Family|Mom`
- `Places|USA|California|San Francisco`

For Finder tags, we usually want just the leaf:
- `Mom`
- `San Francisco`

Otherwise tags become cluttered and hard to read.

---

## Part 2: Command-Line Interface

Now let's build a proper CLI tool that can process multiple files and folders.

### Step 7: Processing Directories Recursively

Add directory processing:

```python
import os


def process_folder(folder_path, merge=True, verbose=False, 
                   strip_prefixes=True):
    """
    Recursively process all supported files in a folder.
    
    Args:
        folder_path: Path to the folder
        merge: If True, merge with existing tags
        verbose: If True, print details for each file
        strip_prefixes: If True, strip hierarchical prefixes
        
    Returns:
        Tuple of (processed, tagged, errors)
    """
    folder_path = Path(folder_path)
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.tiff', '.tif',
        '.raw', '.cr2', '.cr3', '.nef', '.dng',
        '.mov', '.mp4', '.avi', '.mkv'
    }
    
    processed = 0
    tagged = 0
    errors = 0
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip unsupported file types
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            
            processed += 1
            
            # Process the file
            success, keywords = process_file(
                file_path, 
                merge=merge,
                strip_prefixes=strip_prefixes
            )
            
            if not success:
                errors += 1
                if verbose:
                    print(f"  ERROR: {file_path.name}")
            elif keywords:
                tagged += 1
                if verbose:
                    print(f"  {file_path.name}: {', '.join(keywords)}")
    
    return processed, tagged, errors
```

**Understanding os.walk():**

```python
for root, dirs, files in os.walk(folder_path):
```
- `os.walk()` - Recursively traverse directory tree
- `root` - Current directory path
- `dirs` - Subdirectories in current directory
- `files` - Files in current directory

**Example:**
```
Photos/
├── 2024/
│   ├── January/
│   │   └── photo1.jpg
│   └── photo2.jpg
└── photo3.jpg
```

os.walk produces:
1. `root='Photos', dirs=['2024'], files=['photo3.jpg']`
2. `root='Photos/2024', dirs=['January'], files=['photo2.jpg']`
3. `root='Photos/2024/January', dirs=[], files=['photo1.jpg']`

### Step 8: Adding Command-Line Arguments

Use Python's `argparse` module to handle command-line options:

```python
import argparse


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description='Sync Adobe Bridge keywords to macOS Finder tags',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 bridge_keywords_to_tags.py photo.jpg
  python3 bridge_keywords_to_tags.py ~/Pictures -v
  python3 bridge_keywords_to_tags.py ~/Pictures -n -v
        '''
    )
    
    # Positional argument (required)
    parser.add_argument(
        'path',
        help='File or directory to process'
    )
    
    # Optional flags
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output for each file'
    )
    
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    
    parser.add_argument(
        '-r', '--replace',
        action='store_true',
        help='Replace existing tags instead of merging'
    )
    
    parser.add_argument(
        '--keep-prefixes',
        action='store_true',
        help='Keep hierarchical keyword prefixes'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert path to Path object
    path = Path(args.path).expanduser().resolve()
    
    # Check if path exists
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return 1
    
    # Process file or folder
    if path.is_file():
        # Single file
        print(f"Processing file: {path}")
        keywords = get_xmp_keywords(
            path, 
            strip_prefixes=not args.keep_prefixes
        )
        
        if not keywords:
            print("No keywords found")
            return 0
        
        print(f"Found keywords: {', '.join(keywords)}")
        
        if not args.dry_run:
            success, _ = process_file(
                path,
                merge=not args.replace,
                strip_prefixes=not args.keep_prefixes
            )
            if success:
                print("✓ Tags applied successfully")
            else:
                print("✗ Failed to apply tags")
                return 1
        else:
            print("(Dry run - no changes made)")
            
    elif path.is_dir():
        # Directory
        print(f"Processing directory: {path}")
        
        if not args.dry_run:
            processed, tagged, errors = process_folder(
                path,
                merge=not args.replace,
                verbose=args.verbose,
                strip_prefixes=not args.keep_prefixes
            )
            
            print(f"\nSummary:")
            print(f"  Processed: {processed} files")
            print(f"  Tagged: {tagged} files")
            if errors:
                print(f"  Errors: {errors} files")
        else:
            print("(Dry run mode)")
            # In dry run, just show what would be done
            # Implementation left as exercise
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
```

**Understanding argparse:**

```python
parser.add_argument('-v', '--verbose', action='store_true')
```
- First arg: short form (`-v`)
- Second arg: long form (`--verbose`)
- `action='store_true'`: Creates boolean flag (True if present, False if not)

```python
path = Path(args.path).expanduser().resolve()
```
- `expanduser()`: Converts `~` to home directory
- `resolve()`: Converts to absolute path

**Test the CLI:**
```bash
# Process single file
python3 bridge_keywords_to_tags.py photo.jpg -v

# Process directory
python3 bridge_keywords_to_tags.py ~/Pictures -v

# Dry run
python3 bridge_keywords_to_tags.py ~/Pictures -n -v
```

---

## Part 3: Background Service

Now let's make it watch folders automatically and sync in real-time.

### Step 9: Watching for File Changes

We'll use `fswatch` to monitor file system events:

```python
def watch_directories(watch_paths, merge=True, verbose=False, 
                     strip_prefixes=True):
    """
    Watch directories for changes and auto-sync keywords.
    
    Args:
        watch_paths: List of directory paths to watch
        merge: If True, merge with existing tags
        verbose: If True, print details
        strip_prefixes: If True, strip hierarchical prefixes
    """
    print("Starting file watcher...")
    print(f"Watching {len(watch_paths)} director(ies):")
    for path in watch_paths:
        print(f"  - {path}")
    
    # Do initial scan
    print("\nPerforming initial scan...")
    for watch_path in watch_paths:
        if watch_path.is_dir():
            process_folder(
                watch_path,
                merge=merge,
                verbose=verbose,
                strip_prefixes=strip_prefixes
            )
    
    print("\nWatching for changes...\n")
    
    # Track last modification times to avoid duplicates
    last_processed = {}
    
    # Build fswatch command
    # -r = recursive, monitor subdirectories
    # --event Updated = only watch for file modifications
    # --event Created = watch for new files
    fswatch_cmd = [
        'fswatch',
        '-r',
        '--event', 'Updated',
        '--event', 'Created'
    ] + [str(p) for p in watch_paths]
    
    try:
        # Start fswatch process
        process = subprocess.Popen(
            fswatch_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Process each file change as it happens
        for line in process.stdout:
            changed_path = Path(line.strip())
            
            # Skip if not a supported file
            if changed_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            
            # Skip if file doesn't exist (might have been deleted)
            if not changed_path.exists():
                continue
            
            # Check modification time to avoid duplicate processing
            try:
                mtime = changed_path.stat().st_mtime
                last_mtime = last_processed.get(changed_path, 0)
                
                # Only process if modified more than 1 second ago
                # (avoids processing while file is still being written)
                if mtime - last_mtime < 1:
                    continue
                
                last_processed[changed_path] = mtime
                
                # Process the file
                success, keywords = process_file(
                    changed_path,
                    merge=merge,
                    strip_prefixes=strip_prefixes
                )
                
                if success and keywords and verbose:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {changed_path.name}: "
                          f"{', '.join(keywords)}")
                          
            except Exception as e:
                if verbose:
                    print(f"Error processing {changed_path}: {e}")
                    
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        process.terminate()
```

**Understanding fswatch:**

```python
fswatch -r --event Updated --event Created /path/to/watch
```
- `-r`: Recursive (watch subdirectories)
- `--event Updated`: Trigger when files are modified
- `--event Created`: Trigger when files are created
- Output: Prints one file path per line when events occur

**Debouncing:**

```python
if mtime - last_mtime < 1:
    continue
```
- Files might trigger multiple events while being written
- Only process if modified more than 1 second ago
- Prevents duplicate processing

**Add to main():**

```python
# In main(), add watch flag
parser.add_argument(
    '-w', '--watch',
    action='store_true',
    help='Watch directory for changes and auto-sync'
)

# In directory processing section
elif path.is_dir():
    if args.watch:
        # Watch mode
        watch_directories(
            [path],
            merge=not args.replace,
            verbose=args.verbose,
            strip_prefixes=not args.keep_prefixes
        )
    else:
        # One-time processing
        # ... existing code ...
```

**Test watch mode:**
```bash
python3 bridge_keywords_to_tags.py ~/Pictures --watch -v
```

Leave it running, then:
1. Open Adobe Bridge
2. Add keywords to a photo
3. Save
4. Watch the terminal - it should detect the change!

Press Ctrl+C to stop.

### Step 10: Background Service with launchd

macOS uses `launchd` to run background services. We need to create a `.plist` file.

Add to your script:

```python
def get_launchd_plist_path():
    """Get path to the launchd plist file"""
    return Path.home() / "Library" / "LaunchAgents" / \
           "com.user.bridge-keywords-watcher.plist"


def create_launchd_plist(script_path, watch_dirs):
    """
    Create a launchd plist file for the watcher service.
    
    Args:
        script_path: Path to this Python script
        watch_dirs: List of directories to watch
    """
    plist_path = get_launchd_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build command arguments
    args = [
        '/usr/bin/python3',
        '-u',  # Unbuffered output
        str(script_path.resolve()),
        '--watch-service'  # Special flag for service mode
    ]
    
    # Build XML
    args_xml = ''.join(f'<string>{arg}</string>\n        ' 
                       for arg in args)
    
    log_dir = Path.home() / "Library" / "Logs"
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
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
    
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    return plist_path


def service_install(script_path, autostart=False):
    """Install the background service"""
    # Get watch directories from config
    watch_paths = get_configured_watch_paths()
    
    if not watch_paths:
        print("Error: No watch directories configured")
        return False
    
    # Create plist
    plist_path = create_launchd_plist(script_path, watch_paths)
    print(f"✓ Service plist created at: {plist_path}")
    
    if autostart:
        # Modify plist to start on login
        # ... implementation details ...
        pass
    
    print("✓ Service installed")
    print("\nUse these commands to control it:")
    print("  service-start   - Start the service")
    print("  service-stop    - Stop the service")
    print("  service-status  - Check if running")
    
    return True


def service_start():
    """Start the background service"""
    plist_path = get_launchd_plist_path()
    
    if not plist_path.exists():
        print("Service not installed. Run 'service-install' first.")
        return False
    
    subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
    print("✓ Service started")
    return True


def service_stop():
    """Stop the background service"""
    plist_path = get_launchd_plist_path()
    
    subprocess.run(['launchctl', 'unload', str(plist_path)], check=True)
    print("✓ Service stopped")
    return True


def service_status():
    """Check if service is running"""
    result = subprocess.run(
        ['launchctl', 'list'],
        capture_output=True,
        text=True
    )
    
    if 'com.user.bridge-keywords-watcher' in result.stdout:
        return 'running'
    elif get_launchd_plist_path().exists():
        return 'stopped'
    else:
        return 'not-installed'
```

**Understanding launchd:**

- `launchctl load` - Start a service
- `launchctl unload` - Stop a service
- `launchctl list` - Show running services
- `.plist` file describes how to run the service

**Key plist fields:**

- `Label` - Unique identifier
- `ProgramArguments` - Command to run
- `KeepAlive` - Restart if it crashes
- `RunAtLoad` - Start automatically on login (true/false)
- `StandardOutPath` - Where to save output logs

**Add service commands to main():**

```python
# Add special handling for service commands
if len(sys.argv) > 1:
    command = sys.argv[1]
    
    if command == 'service-install':
        return service_install(Path(__file__))
    elif command == 'service-start':
        return 0 if service_start() else 1
    elif command == 'service-stop':
        return 0 if service_stop() else 1
    elif command == 'service-status':
        status = service_status()
        print(f"Service status: {status}")
        return 0
    elif command == '--watch-service':
        # Started by launchd
        watch_paths = get_configured_watch_paths()
        watch_directories(watch_paths, from_service=True)
        return 0

# ... rest of argparse code ...
```

**Using the service:**

```bash
# Install
python3 bridge_keywords_to_tags.py service-install

# Start
python3 bridge_keywords_to_tags.py service-start

# Check status
python3 bridge_keywords_to_tags.py service-status

# View logs
tail -f ~/Library/Logs/bridge-keywords-watcher.log

# Stop
python3 bridge_keywords_to_tags.py service-stop
```

---

## Part 4: Menu Bar Application

Let's create a menu bar app for easy control.

### Step 11: Introduction to rumps

`rumps` (Ridiculously Uncomplicated macOS Python Statusbar apps) makes menu bar apps easy.

**Basic example:**

```python
import rumps

class HelloApp(rumps.App):
    def __init__(self):
        super(HelloApp, self).__init__("Hello")
        self.menu = ["Say Hi"]
    
    @rumps.clicked("Say Hi")
    def say_hi(self, _):
        rumps.notification("Hello", "Hi!", "Nice to meet you!")

if __name__ == '__main__':
    HelloApp().run()
```

Save as `hello_menubar.py` and run:
```bash
python3 hello_menubar.py
```

You'll see "Hello" appear in your menu bar!

### Step 12: Building the Bridge Menu Bar App

Create `bridge_menubar.py`:

```python
#!/usr/bin/env python3
"""
Bridge Keywords to Tags - Menu Bar Application
"""
import rumps
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Import our main script functions
import bridge_keywords_to_tags as bkt


class BridgeMenuBarApp(rumps.App):
    def __init__(self):
        # Initialize with name that appears in menu bar
        super(BridgeMenuBarApp, self).__init__(
            "Bridge",  # Text in menu bar
            icon=None,  # Optional icon
            quit_button=None  # We'll add custom Quit
        )
        
        # Track state
        self.is_running = False
        self.last_check = None
        
        # Build menu
        self.menu = [
            rumps.MenuItem("Service Status", callback=self.show_status),
            rumps.MenuItem("Show Config", callback=self.show_config),
            None,  # Separator
            rumps.MenuItem("Start Service", callback=self.start_service),
            rumps.MenuItem("Stop Service", callback=self.stop_service),
            rumps.MenuItem("Restart Service", callback=self.restart_service),
            None,
            rumps.MenuItem("View Logs", callback=self.view_logs),
            rumps.MenuItem("Open Configuration", callback=self.open_config),
            None,
            rumps.MenuItem("Process Current Directory", 
                          callback=self.process_current),
            None,
            rumps.MenuItem("About", callback=self.show_about),
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
        
        # Start status update timer (every 5 seconds)
        self.timer = rumps.Timer(self.update_status, 5)
        self.timer.start()
        
        # Do initial status check
        self.update_status(None)
    
    def update_status(self, _):
        """Update service status and menu bar icon"""
        status = bkt.service_status()
        
        if status == 'running':
            self.is_running = True
            self.title = "Bridge ✓"  # Green checkmark
            self.menu["Start Service"].set_callback(None)  # Disable
            self.menu["Stop Service"].set_callback(self.stop_service)
            self.menu["Restart Service"].set_callback(self.restart_service)
        elif status == 'stopped':
            self.is_running = False
            self.title = "Bridge ○"  # Empty circle
            self.menu["Start Service"].set_callback(self.start_service)
            self.menu["Stop Service"].set_callback(None)  # Disable
            self.menu["Restart Service"].set_callback(None)
        else:  # not-installed
            self.is_running = False
            self.title = "Bridge"
            self.menu["Start Service"].set_callback(self.start_service)
            self.menu["Stop Service"].set_callback(None)
            self.menu["Restart Service"].set_callback(None)
        
        self.last_check = datetime.now()
    
    @rumps.clicked("Service Status")
    def show_status(self, _):
        """Show detailed status"""
        status = bkt.service_status()
        watch_paths = bkt.get_configured_watch_paths()
        
        if status == 'running':
            status_text = "🟢 Running"
        elif status == 'stopped':
            status_text = "⚪ Stopped"
        else:
            status_text = "⚫ Not installed"
        
        dirs_text = f"{len(watch_paths)} director(ies)"
        
        rumps.notification(
            title=f"Bridge: {status_text}",
            subtitle=dirs_text,
            message=f"Last checked: {self.last_check.strftime('%H:%M:%S')}"
        )
    
    @rumps.clicked("Start Service")
    def start_service(self, _):
        """Start the background service"""
        def start_async():
            try:
                if bkt.service_start():
                    rumps.notification(
                        title="Service Started",
                        subtitle="Bridge Keywords to Tags",
                        message="Now monitoring for changes"
                    )
                    self.update_status(None)
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Failed to start service",
                    message=str(e)
                )
        
        # Run in background thread (don't freeze menu)
        threading.Thread(target=start_async, daemon=True).start()
    
    @rumps.clicked("Stop Service")
    def stop_service(self, _):
        """Stop the background service"""
        def stop_async():
            try:
                if bkt.service_stop():
                    rumps.notification(
                        title="Service Stopped",
                        subtitle="Bridge Keywords to Tags",
                        message="No longer monitoring"
                    )
                    self.update_status(None)
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Failed to stop service",
                    message=str(e)
                )
        
        threading.Thread(target=stop_async, daemon=True).start()
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """Open logs in Console.app"""
        log_path = Path.home() / "Library" / "Logs" / \
                   "bridge-keywords-watcher.log"
        
        if log_path.exists():
            subprocess.run(['open', '-a', 'Console', str(log_path)])
        else:
            rumps.notification(
                title="No Logs Found",
                subtitle="Bridge Keywords to Tags",
                message="Service hasn't been started yet"
            )
    
    @rumps.clicked("Process Current Directory")
    def process_current(self, _):
        """Process the current Finder directory"""
        def process_async():
            try:
                # Get current Finder directory using AppleScript
                applescript = '''
                tell application "Finder"
                    if (count of Finder windows) is 0 then
                        return POSIX path of (desktop as alias)
                    else
                        return POSIX path of (target of front window as alias)
                    end if
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    rumps.notification(
                        title="Error",
                        subtitle="Could not get Finder directory",
                        message=""
                    )
                    return
                
                current_dir = Path(result.stdout.strip())
                
                # Process it
                script_path = Path(__file__).parent / \
                             "bridge_keywords_to_tags.py"
                
                subprocess.Popen([
                    'python3',
                    str(script_path),
                    str(current_dir),
                    '-v'
                ])
                
                rumps.notification(
                    title="Processing Started",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Processing files in {current_dir.name}"
                )
                
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Processing failed",
                    message=str(e)
                )
        
        threading.Thread(target=process_async, daemon=True).start()
    
    @rumps.clicked("About")
    def show_about(self, _):
        """Show about info"""
        rumps.notification(
            title="Bridge Keywords to Tags",
            subtitle="Menu Bar Application",
            message="Sync Adobe Bridge keywords to Finder tags"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the menu bar app"""
        rumps.quit_application()


if __name__ == '__main__':
    BridgeMenuBarApp().run()
```

**Understanding rumps:**

```python
@rumps.clicked("Menu Item Text")
def handler(self, _):
```
- Decorator links function to menu item
- Second parameter is the sender (we don't use it, so `_`)

```python
threading.Thread(target=function, daemon=True).start()
```
- Run function in background thread
- Prevents freezing the menu bar
- `daemon=True` means thread dies when app quits

```python
rumps.notification(title, subtitle, message)
```
- Shows macOS notification
- Non-blocking (doesn't wait for user)

**Run it:**
```bash
python3 bridge_menubar.py
```

---

## Part 5: GUI Dashboard

Now let's build a visual dashboard using tkinter.

### Step 13: Introduction to tkinter

tkinter is Python's standard GUI library.

**Basic window:**

```python
import tkinter as tk

root = tk.Tk()
root.title("My App")
root.geometry("400x300")

label = tk.Label(root, text="Hello, GUI!")
label.pack()

button = tk.Button(root, text="Click Me", 
                   command=lambda: print("Clicked!"))
button.pack()

root.mainloop()
```

Save as `gui_test.py` and run:
```bash
python3 gui_test.py
```

### Step 14: Building the Dashboard

Create `bridge_dashboard_gui.py`:

```python
#!/usr/bin/env python3
"""
Bridge Keywords to Tags - GUI Dashboard
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
from pathlib import Path
from datetime import datetime
import threading

# Import main script
import bridge_keywords_to_tags as bkt


class BridgeDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Bridge Keywords to Tags - Dashboard")
        
        # Set size and position
        window_width = 750
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create UI
        self.create_widgets()
        
        # Initial refresh
        self.refresh_status()
        
        # Auto-refresh every 10 seconds
        self.auto_refresh()
    
    def create_widgets(self):
        """Build the UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        title = ttk.Label(
            main_frame,
            text="Bridge Keywords to Tags",
            font=('Helvetica', 18, 'bold')
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.LabelFrame(
            main_frame,
            text="Status",
            padding="10"
        )
        status_frame.grid(row=1, column=0, columnspan=3,
                         sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Checking...",
            font=('Helvetica', 12)
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(
            main_frame,
            text="Configuration",
            padding="10"
        )
        config_frame.grid(row=2, column=0, columnspan=3,
                         sticky=(tk.W, tk.E), pady=5)
        
        self.config_text = tk.Text(
            config_frame,
            height=6,
            width=60,
            font=('Monaco', 10),
            relief=tk.FLAT,
            background='#ffffff',
            foreground='#000000'
        )
        self.config_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.config_text.config(state=tk.DISABLED)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(
            button_frame,
            text="Start Service",
            command=self.start_service,
            width=15
        )
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="Stop Service",
            command=self.stop_service,
            width=15
        )
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_status,
            width=15
        ).grid(row=0, column=2, padx=5)
        
        # Logs frame
        logs_frame = ttk.LabelFrame(
            main_frame,
            text="Recent Logs",
            padding="10"
        )
        logs_frame.grid(row=4, column=0, columnspan=3,
                       sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=15,
            font=('Monaco', 9)
        )
        self.log_text.grid(row=0, column=0,
                          sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_bar = ttk.Label(
            main_frame,
            text="Ready",
            relief=tk.SUNKEN
        )
        self.status_bar.grid(row=5, column=0, columnspan=3,
                            sticky=(tk.W, tk.E), pady=(5, 0))
    
    def refresh_status(self):
        """Refresh all information"""
        def refresh_thread():
            try:
                # Get service status
                status = bkt.service_status()
                
                # Update status display
                if status == 'running':
                    status_text = "🟢 Running"
                    status_color = 'green'
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                elif status == 'stopped':
                    status_text = "⚪ Stopped"
                    status_color = 'orange'
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                else:
                    status_text = "⚫ Not installed"
                    status_color = 'red'
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                
                self.root.after(0, lambda: self.status_label.config(
                    text=status_text,
                    foreground=status_color
                ))
                
                # Update config display
                watch_paths = bkt.get_configured_watch_paths()
                config_text = f"Watched directories: {len(watch_paths)}\n"
                for path in watch_paths:
                    config_text += f"  - {path}\n"
                
                self.root.after(0, lambda: self.update_config(config_text))
                
                # Load logs
                self.root.after(0, self.load_logs)
                
                # Update status bar
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Last updated: {timestamp}"
                ))
                
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"
                ))
        
        # Run in background thread
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def update_config(self, text):
        """Update config text widget"""
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, text)
        self.config_text.config(state=tk.DISABLED)
    
    def load_logs(self):
        """Load recent logs"""
        log_path = Path.home() / "Library" / "Logs" / \
                   "bridge-keywords-watcher.log"
        
        if not log_path.exists():
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, "No logs available")
            return
        
        # Read last 100 lines
        result = subprocess.run(
            ['tail', '-100', str(log_path)],
            capture_output=True,
            text=True
        )
        
        self.log_text.delete(1.0, tk.END)
        if result.stdout:
            self.log_text.insert(1.0, result.stdout)
            self.log_text.see(tk.END)  # Scroll to bottom
    
    def start_service(self):
        """Start the service"""
        def start_thread():
            try:
                if bkt.service_start():
                    self.root.after(0, lambda: self.status_bar.config(
                        text="Service started successfully"
                    ))
                    self.root.after(1000, self.refresh_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"
                ))
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_service(self):
        """Stop the service"""
        def stop_thread():
            try:
                if bkt.service_stop():
                    self.root.after(0, lambda: self.status_bar.config(
                        text="Service stopped successfully"
                    ))
                    self.root.after(1000, self.refresh_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"
                ))
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def auto_refresh(self):
        """Auto-refresh every 10 seconds"""
        self.refresh_status()
        self.root.after(10000, self.auto_refresh)


def main():
    root = tk.Tk()
    app = BridgeDashboard(root)
    root.mainloop()


if __name__ == '__main__':
    main()
```

**Understanding tkinter layout:**

```python
widget.grid(row=0, column=0, sticky=(tk.W, tk.E))
```
- `grid()` - Position widget in a grid
- `row`, `column` - Which cell
- `sticky` - Which edges to stick to (W=west, E=east, N=north, S=south)

```python
self.root.after(0, lambda: function())
```
- Schedule function to run on main thread
- GUI updates must happen on main thread
- `0` means run as soon as possible

**Threading in GUIs:**

```python
def refresh_status(self):
    def refresh_thread():
        # Do slow work here
        result = slow_operation()
        
        # Update GUI on main thread
        self.root.after(0, lambda: update_gui(result))
    
    threading.Thread(target=refresh_thread, daemon=True).start()
```

This pattern:
1. Starts background thread for slow work
2. Doesn't freeze the GUI
3. Updates GUI safely on main thread

**Run it:**
```bash
python3 bridge_dashboard_gui.py
```

---

## Part 6: App Bundle

Finally, let's package everything as a native macOS app.

### Step 15: Creating the App Bundle

Follow the tutorial in `TUTORIAL_Creating_macOS_Apps.md` to:

1. Create the `.app` directory structure
2. Write `Info.plist`
3. Create launcher script
4. Copy Python scripts to Resources
5. Add an icon

The result: `Bridge Keywords to Tags.app`

---

## Testing and Debugging

### General Debugging Tips

**Print Debugging:**
```python
print(f"Debug: variable = {variable}")
```

**Logging:**
```python
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s'
)

logging.debug("Debug message")
logging.info("Info message")
logging.error("Error message")
```

**Try/Except:**
```python
try:
    risky_operation()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()  # Print full error details
```

### Testing Strategies

**Unit Testing:**

Create `test_keywords.py`:

```python
import unittest
from bridge_keywords_to_tags import strip_hierarchical_prefix

class TestKeywordFunctions(unittest.TestCase):
    def test_strip_prefix(self):
        # Test normal case
        result = strip_hierarchical_prefix("Cat|Sub|Item")
        self.assertEqual(result, "Item")
        
        # Test no prefix
        result = strip_hierarchical_prefix("Simple")
        self.assertEqual(result, "Simple")
        
        # Test empty
        result = strip_hierarchical_prefix("")
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
```

Run: `python3 test_keywords.py`

**Integration Testing:**

```bash
# Create test file
echo "test" > test.jpg

# Add keywords with exiftool
exiftool -Keywords="test,photo" test.jpg

# Run your script
python3 bridge_keywords_to_tags.py test.jpg

# Verify tags were set
xattr -p com.apple.metadata:_kMDItemUserTags test.jpg
```

---

## Next Steps

### Enhancements to Try

1. **Add more file formats** - Support more RAW formats
2. **Color tags** - Assign colors to specific keywords
3. **Batch operations** - Process multiple directories
4. **Smart folders** - Create saved searches
5. **Sync stats** - Track how many files processed
6. **Conflict resolution** - Handle duplicate keywords
7. **Export/import** - Backup and restore tags

### Learning Resources

**Python:**
- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/)

**macOS Development:**
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [PyObjC](https://pyobjc.readthedocs.io/) - Python-macOS bridge

**tkinter:**
- [TkDocs](https://tkdocs.com/tutorial/)
- [Tcl/Tk Documentation](https://www.tcl.tk/man/tcl8.6/)

**General:**
- [Stack Overflow](https://stackoverflow.com/) - Ask questions
- [GitHub](https://github.com/) - Study other projects

### Contributing

If you improve the application:
1. Use version control (git)
2. Write tests for new features
3. Document your changes
4. Share with others!

---

## Conclusion

You've learned how to build a complete macOS application from scratch!

**Skills gained:**
- Python programming
- File system operations
- XMP metadata handling
- macOS integration
- GUI development
- Background services
- App bundling

**Key concepts:**
- Separation of concerns (core engine, CLI, GUI, service)
- Threading for responsive UIs
- Error handling and logging
- Testing strategies

**Remember:**
- Start simple, add features gradually
- Test frequently
- Read error messages carefully
- Use print debugging liberally
- Google is your friend!

Good luck building your own applications!
