# Bridge Keywords to Tags

A Python script that copies Adobe Bridge/XMP keywords from image files to macOS Finder tags, making your metadata searchable in Finder and Spotlight.

## What It Does

This script reads keywords embedded in image files (added via Adobe Bridge, Lightroom, or other photo management software) and applies them as native macOS Finder tags. This allows you to:

- Search for images using Finder's tag search
- Find images via Spotlight using their keywords
- Organize files using macOS's built-in tagging system
- Keep your Adobe Bridge keywords synchronized with macOS tags

## Requirements

- **macOS** (uses Finder tags and launchd)
- **Python 3** with Anaconda or system Python
- **exiftool** (for reading image metadata)
- **fswatch** (for file system monitoring)
- **rumps** (for menu bar app)

## Installation

Install required dependencies:

```bash
# Install command-line tools via Homebrew
brew install exiftool fswatch

# Install Python package for menu bar
pip3 install rumps --user
```

If you don't have Homebrew, install it from [brew.sh](https://brew.sh)

## macOS Application

**Bridge Keywords to Tags.app** - Complete macOS application with menu bar and GUI dashboard.

### Installation

The app is located at:
```
/Users/nica/python-scripts/Bridge Keywords Sync/Bridge Keywords to Tags.app
```

**To use:**
1. Double-click to launch (or drag to Applications folder)
2. The Bridge icon appears in your menu bar
3. Click the icon to access all features

**Optional: Auto-start at login**
- Click Bridge menu → "Automatically open ✓" to toggle
- Or: System Settings → General → Login Items → Add "Bridge Keywords to Tags.app"

### Menu Bar Features

**Status Monitoring:**
- Visual indicator: "Bridge ✓" (running), "Bridge ○" (stopped), "Bridge" (not installed)
- Service Status - Detailed status with watched directories
- Show Config - View current settings

**Service Controls:**
- Start/Stop/Restart Service
- Marker keyword toggle ("sync enabled" / "all enabled")

**Quick Actions:**
- Process Current Directory - Sync keywords for current Finder folder
- Stop Processing - Kill any running processing tasks
- View Logs - Opens log file in Console.app
- Open Configuration - Edit settings in text editor

**Dashboard:**
- Opens GUI dashboard for comprehensive management

### GUI Dashboard

Launch from Bridge menu → Dashboard or run directly:
```bash
python3 bridge_dashboard_gui.py
```

**Features:**
- Real-time service status with color indicators
- View current configuration (strip prefixes, replace mode, marker keyword)
- **Watched Directories Manager:**
  - Add directories with native macOS folder picker
  - Remove directories with one click
  - Changes take effect immediately
- Service control buttons (Start/Stop/Restart/Refresh)
- Live log viewer (last 100 lines, auto-refresh every 10 seconds)
- Status bar with last update time
- 750x800 window, centered on screen

**Window automatically comes to front** after adding folders.

## Usage

### Basic Syntax

```bash
python3 bridge_keywords_to_tags.py <path> [options]
```

### Arguments

- `path` - A single file or directory to process
  - **File**: Process one specific image
  - **Directory**: Recursively process all supported images in the directory

### Options

- `-c, --check` - Display keywords embedded in files without applying any tags (useful for verification)
- `-n, --dry-run` - Show what would be done without making changes
- `-r, --replace` - Replace existing tags instead of merging with them
- `-v, --verbose` - Show detailed output for each file processed
- `-w, --watch` - Watch directory for changes and automatically sync keywords to tags (background monitoring)
- `--keep-prefixes` - Keep hierarchical keyword prefixes (e.g., `Category|Keyword` instead of just `Keyword`)

## Examples

### Process a single file

```bash
python3 bridge_keywords_to_tags.py "Heritage hero col.jpg" -v
```

### Process an entire directory

```bash
python3 bridge_keywords_to_tags.py /Users/nica/Downloads -v
```

### Preview changes without applying them

```bash
python3 bridge_keywords_to_tags.py /Users/nica/Downloads -n -v
```

### Replace existing tags (don't merge)

```bash
python3 bridge_keywords_to_tags.py /Users/nica/Downloads -r -v
```

### Process multiple specific files

Use a loop to process multiple individual files:

```bash
for file in "file1.jpg" "file2.jpg" "file3.jpg"; do
  python3 bridge_keywords_to_tags.py "$file" -v
done
```

### Check keywords without applying tags

```bash
# Check a single file
python3 bridge_keywords_to_tags.py "Winslow hero col.jpg" --check

# Check all files in a directory
python3 bridge_keywords_to_tags.py /Users/nica/Downloads --check
```

### Watch mode - Automatic background monitoring

Monitor a directory for changes and automatically sync keywords to tags:

```bash
# Watch a directory (press Ctrl+C to stop)
python3 bridge_keywords_to_tags.py ~/Pictures --watch

# Watch with verbose output
python3 bridge_keywords_to_tags.py ~/Pictures --watch -v

# Watch and replace tags instead of merging
python3 bridge_keywords_to_tags.py ~/Pictures --watch -r
```

Watch mode will:
- Perform an initial scan of all files
- Monitor for file changes (creation and updates)
- Automatically sync keywords when files are modified in Adobe Bridge
- Run continuously until stopped with Ctrl+C

## Background Service Configuration

For persistent monitoring, you can configure directories to watch and run the service automatically.

### 1. Configure Watch Directories

Edit the `bridge_keywords_to_tags.py` file and find the `WATCH CONFIGURATION` section at the top:

```python
# ============================================================================
# WATCH CONFIGURATION - Edit the directories you want to monitor
# ============================================================================
WATCH_DIRECTORIES = [
    "/Users/nica/Pictures",
    "/Users/nica/Documents/Photos",
]

# Set to True to replace existing tags, False to merge with existing tags
WATCH_REPLACE_MODE = False

# Strip parent prefixes from hierarchical keywords (e.g., "Other Keywords|hero" -> "hero")
# Set to True to use only the leaf keyword, False to keep the full path
STRIP_HIERARCHICAL_PREFIXES = True

# Marker keyword - only process files with this keyword in their XMP metadata
# Set to None to process all files with keywords, or a string like "sync" to require it
MARKER_KEYWORD = "sync"
# ============================================================================
```

Add or remove directories as needed. The service will monitor all configured directories.

### Marker Keyword (Selective Processing)

By default, the script is configured to **only process files that have a "sync" keyword** in their Adobe Bridge metadata. This prevents the script from modifying files that came from other sources with existing XMP keywords.

**How it works:**
- Only files with the keyword "sync" will be processed
- The "sync" keyword itself is removed from Finder tags (it's only used as a marker)
- Files without the "sync" keyword are completely ignored, even if they have other keywords

**To use:**
1. In Adobe Bridge, add the keyword "sync" to any file you want to sync to Finder tags
2. Add any other keywords you want as Finder tags
3. Run the script or let the service process the file
4. Only the other keywords (not "sync") will appear as Finder tags

**To disable this feature** and process all files with keywords:
- Edit `bridge_keywords_to_tags.py`
- Find `MARKER_KEYWORD = "sync"`
- Change it to `MARKER_KEYWORD = None`

### 2. Service Management Commands

```bash
# Check configured directories and service status
python3 bridge_keywords_to_tags.py service-status

# Install the service (uses directories from WATCH_DIRECTORIES)
python3 bridge_keywords_to_tags.py service-install

# Install with autostart (starts automatically on login)
python3 bridge_keywords_to_tags.py service-install --autostart

# Start the service
python3 bridge_keywords_to_tags.py service-start

# Stop the service
python3 bridge_keywords_to_tags.py service-stop

# Restart the service (useful after editing WATCH_DIRECTORIES)
python3 bridge_keywords_to_tags.py service-restart

# View service logs
python3 bridge_keywords_to_tags.py service-logs

# Follow logs in real-time
python3 bridge_keywords_to_tags.py service-logs --follow

# Uninstall the service
python3 bridge_keywords_to_tags.py service-uninstall
```

### How the Service Works

- **Configuration**: All watched directories are defined in the `WATCH_DIRECTORIES` section of the script
- **Multiple Directories**: You can watch as many directories as you need
- **On-Demand**: By default, the service is installed but won't start automatically on login
- **Autostart**: Use `--autostart` during installation to start the service automatically when you log in
- **Persistent**: Once started, the service runs continuously and automatically restarts if it crashes
- **Logs**: All output is saved to `~/Library/Logs/bridge-keywords-watcher.log`

### Updating Watch Directories

To add or remove directories:

1. Edit the `WATCH_DIRECTORIES` section in `bridge_keywords_to_tags.py`
2. If the service is installed, reinstall it:
   ```bash
   python3 bridge_keywords_to_tags.py service-uninstall
   python3 bridge_keywords_to_tags.py service-install
   python3 bridge_keywords_to_tags.py service-start
   ```
   
   Or simply restart if it's running:
   ```bash
   python3 bridge_keywords_to_tags.py service-restart
   ```

### Example Workflow

```bash
# 1. Edit the script to add your directories
# Open bridge_keywords_to_tags.py and edit WATCH_DIRECTORIES

# 2. Check the configuration
python3 bridge_keywords_to_tags.py service-status

# 3. Install the service
python3 bridge_keywords_to_tags.py service-install

# 4. Start it when you're working with Adobe Bridge
python3 bridge_keywords_to_tags.py service-start

# 5. Check that it's running
python3 bridge_keywords_to_tags.py service-status

# 6. View what it's doing
python3 bridge_keywords_to_tags.py service-logs --follow

# 7. Stop it when you're done
python3 bridge_keywords_to_tags.py service-stop
```

## Verifying Keywords in Your Files

Before running the script, you can check what keywords are actually embedded in your files.

### Using the built-in --check flag (Recommended)

```bash
# Check keywords in a single file
python3 bridge_keywords_to_tags.py "Winslow hero col.jpg" --check

# Check all files in a directory
python3 bridge_keywords_to_tags.py /Users/nica/Downloads --check
```

### Using exiftool directly

Alternatively, you can use exiftool directly:

```bash
# Single file
exiftool -Keywords -Subject -HierarchicalSubject "Winslow hero col.jpg"

# All JPG files in a directory
exiftool -Keywords -Subject -HierarchicalSubject /Users/nica/Downloads/*.jpg
```

### Understanding the output

```
Keywords                        : hero, collection, front, 11, 2000
Subject                         : hero, collection, front, 11, 2000
Hierarchical Subject            : Other Keywords|11, Other Keywords|2000, Other Keywords|collection
```

- **Keywords/Subject**: Flat keywords that will be used as Finder tags
- **Hierarchical Subject**: Nested keywords (e.g., `Parent|Child`)
  - By default, only the leaf keyword is used (e.g., `Other Keywords|hero` becomes `hero`)
  - Controlled by `STRIP_HIERARCHICAL_PREFIXES` setting in the script
  - Use `--keep-prefixes` flag to keep the full path

### Automatic Hierarchical Prefix Stripping

By default, the script automatically strips parent prefixes from hierarchical keywords:
- `Other Keywords|hero` → `hero`
- `Category|Subcategory|Item` → `Item`

This is controlled by the `STRIP_HIERARCHICAL_PREFIXES` setting in the configuration section (enabled by default).

**To keep full hierarchical paths**, use the `--keep-prefixes` flag:
```bash
python3 bridge_keywords_to_tags.py ~/Pictures --keep-prefixes
```

### Manual Cleanup (Alternative)

If you want to permanently remove hierarchical keywords from your files:

```bash
# Remove hierarchical keywords from a single file
exiftool -HierarchicalSubject= "image.jpg"

# Remove from all JPG files in a directory
exiftool -HierarchicalSubject= /path/to/directory/*.jpg
```

This removes the HierarchicalSubject field entirely while keeping flat keywords (Keywords/Subject fields) intact.

## Supported File Formats

The script processes common image and video formats that support XMP metadata:

- **Images**: JPG, PNG, TIFF, GIF, BMP, PSD, AI, EPS, PDF
- **RAW**: CR2, CR3, NEF, ARW, ORF, RW2, DNG
- **Video**: MOV, MP4, AVI, MKV
- **Sidecar**: XMP files

## How It Works

1. **Read Keywords**: Uses `exiftool` to extract XMP keywords from image metadata fields (Subject, Keywords, HierarchicalSubject)
2. **Merge Tags**: By default, combines existing Finder tags with new keywords (use `-r` to replace instead)
3. **Apply Tags**: Writes tags to the macOS extended attributes using `xattr`

## Default Behavior

- **Merging**: New keywords are added to existing Finder tags (not replaced)
- **Recursive**: When given a directory, processes all subdirectories
- **Safe**: Only processes supported file formats, skips unsupported files

## Troubleshooting

### "exiftool is not installed"

Install exiftool:
```bash
brew install exiftool
```

### "Path does not exist"

Check that the file or directory path is correct. Use quotes for paths with spaces:
```bash
python3 bridge_keywords_to_tags.py "My Photos/image.jpg"
```

### No keywords found

- Ensure your images have keywords added in Adobe Bridge or similar tools
- Try using `-v` to see which files have keywords
- Verify keywords exist by running: `exiftool -Keywords -Subject "image.jpg"`

### Permission errors

Make sure you have read/write permissions for the files you're processing.

## Tips

- **Test first**: Always use `-n -v` flags first to preview changes before applying them
- **Batch processing**: For large directories, run without `-v` to avoid excessive output
- **Backup**: Consider backing up important files before batch processing
- **Selective processing**: To process only specific files in a directory, use a loop with individual file paths

## Example Workflow

```bash
# 1. Check what keywords are embedded in your files
python3 bridge_keywords_to_tags.py ~/Pictures --check

# 2. (Optional) Remove unwanted hierarchical prefixes if needed
exiftool -HierarchicalSubject= "image.jpg"

# 3. Preview what will happen (dry run)
python3 bridge_keywords_to_tags.py ~/Pictures -n -v

# 4. Apply changes to all images
python3 bridge_keywords_to_tags.py ~/Pictures -v

# 5. Verify tags in Finder
# Open Finder, select a file, and press Cmd+I to see tags
```

## License

This script is provided as-is for personal use.
