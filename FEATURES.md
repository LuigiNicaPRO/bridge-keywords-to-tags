# Bridge Keywords to Tags - Features

A comprehensive tool for synchronizing Adobe Bridge/XMP keywords with macOS Finder tags, featuring a native macOS application, GUI dashboard, and powerful command-line interface.

## macOS Application

### Native App Bundle

**Bridge Keywords to Tags.app** - Self-contained macOS application (96KB)

**Features:**
- Double-click to launch from Finder
- Menu bar integration with status indicator
- GUI dashboard for visual management
- Auto-start toggle for login items
- Portable within your system

**Components:**
- Menu bar app (bridge_menubar.py)
- GUI dashboard (bridge_dashboard_gui.py)
- Core sync engine (bridge_keywords_to_tags.py)

### Menu Bar Application

**Always-Available Control Center**
- Lives in your menu bar for instant access
- Visual status indicator: "Bridge ✓" (running), "Bridge ○" (stopped)
- Single-click access to all features
- macOS notification integration
- Singleton instance protection (no duplicate launches)

**Service Management:**
- Start/Stop/Restart background service
- View real-time service status
- Check watched directories and configuration
- Toggle marker keyword mode (sync/all)

**Quick Actions:**
- Process Current Directory - Sync the active Finder folder
- Stop Processing - Kill any running tasks
- View Logs - Open Console.app with service logs
- Open Configuration - Edit settings directly
- Launch Dashboard - Open GUI for detailed management

**Auto-Start Toggle:**
- "Automatically open ✓" menu item
- Creates/removes login item via launchd
- Persists across system restarts
- No manual configuration needed

### GUI Dashboard

**Visual Service Management** (750x800 window)

**Real-Time Monitoring:**
- Color-coded service status (🟢 Running, ⚪ Stopped, ⚫ Not installed)
- Current configuration display
- Live log viewer (last 100 lines)
- Auto-refresh every 10 seconds
- Status bar with last update timestamp

**Watched Directories Manager:**
- Add directories with native macOS folder picker
- Remove directories with single click
- Visual list of all watched paths
- Changes write directly to configuration file
- Automatic module reload after changes

**Service Controls:**
- Start/Stop/Restart buttons
- Manual refresh button
- All operations run asynchronously (non-blocking UI)
- Success/error feedback in status bar

**Window Behavior:**
- Centers on screen at startup
- Automatically comes to front after folder selection
- Proper button anchoring (no clickability issues at different widths)
- Native macOS Aqua theme integration

## Core Features

### 1. Keyword Synchronization

**Automatic Metadata Migration**
- Extracts keywords from Adobe Bridge, Lightroom, and other XMP-compatible applications
- Copies keywords to macOS Finder tags for system-wide searchability
- Works with Keywords, Subject, and HierarchicalSubject XMP fields
- Handles both flat keywords and hierarchical structures

**Tag Merge Modes**
- **Merge Mode** (default): Adds new keywords while preserving existing Finder tags
- **Replace Mode**: Overwrites existing tags with keywords from files

### 2. Wide File Format Support

**Image Formats**
- JPEG, PNG, TIFF, GIF, BMP
- Adobe formats: PSD, AI, EPS
- PDF documents

**RAW Camera Formats**
- Canon: CR2, CR3
- Nikon: NEF
- Sony: ARW
- Olympus: ORF
- Panasonic: RW2
- Adobe: DNG
- Generic RAW

**Video Formats**
- MOV, MP4, AVI, MKV

**Sidecar Files**
- XMP sidecar files (automatically applies to associated media files)

### 3. Processing Modes

#### Single File Processing
Process individual files with full control over merge behavior:
```bash
python3 bridge_keywords_to_tags.py "photo.jpg"
```

#### Batch Directory Processing
Recursively process all supported files in a directory and its subdirectories:
```bash
python3 bridge_keywords_to_tags.py ~/Pictures -v
```

#### Dry Run Mode
Preview what changes will be made without modifying any files:
```bash
python3 bridge_keywords_to_tags.py ~/Pictures -n -v
```

### 4. Keyword Verification

**Built-in Inspection Tool**
View all keywords embedded in files before processing:
```bash
python3 bridge_keywords_to_tags.py "photo.jpg" --check
```

**Output Format**
- Displays Keywords, Subject, and HierarchicalSubject fields separately
- Shows all metadata values including mixed data types (text and numbers)
- Works on single files or entire directories

**Use Cases**
- Verify keywords exist before syncing
- Identify unwanted hierarchical prefixes
- Troubleshoot missing or incorrect metadata
- Audit keyword consistency across files

### 5. Real-Time Monitoring (Watch Mode)

**Interactive Watch Mode**
Monitor directories in real-time from the command line:
```bash
python3 bridge_keywords_to_tags.py ~/Pictures --watch -v
```

**Features**
- Performs initial scan of all existing files
- Monitors for file creation and modification events
- Automatically syncs keywords when files are updated in Adobe Bridge
- Timestamped activity log
- Press Ctrl+C to stop

**Smart Processing**
- Debounces rapid file changes to avoid duplicate processing
- Skips incomplete file writes
- Only processes supported file formats
- Handles errors gracefully without stopping

### 6. Background Service

**macOS launchd Integration**
Run the watcher as a persistent background service:
```bash
python3 bridge_keywords_to_tags.py service-install
python3 bridge_keywords_to_tags.py service-start
```

**Configuration-Based Setup**
- Edit `WATCH_DIRECTORIES` in the script to configure monitored folders
- Support for unlimited directories simultaneously
- Simple Python list syntax for easy editing
- Global `WATCH_REPLACE_MODE` setting

**Service Management**
- `service-status` - Check if service is running and view configuration
- `service-start` - Start the background service
- `service-stop` - Stop the background service
- `service-restart` - Restart after configuration changes
- `service-logs` - View activity logs
- `service-logs --follow` - Real-time log monitoring
- `service-uninstall` - Remove the service

**Startup Options**
- **On-Demand** (default): Service installed but doesn't start automatically
- **Auto-Start**: Use `--autostart` flag to run on login

**Reliability**
- Automatic restart on crashes (via launchd KeepAlive)
- Persistent across reboots when auto-start is enabled
- Comprehensive logging to `~/Library/Logs/bridge-keywords-watcher.log`
- Separate error log for troubleshooting

### 7. Hierarchical Keyword Support

**Automatic Prefix Stripping**
- Automatically strips parent prefixes from hierarchical keywords (enabled by default)
- Converts `Other Keywords|hero` to just `hero`
- Converts `Category|Subcategory|Item` to just `Item`
- Uses only the leaf keyword for cleaner Finder tags
- Controlled by `STRIP_HIERARCHICAL_PREFIXES` configuration setting

**Full Path Preservation**
- Use `--keep-prefixes` flag to preserve full hierarchical paths
- Example: Keep `Category|Subcategory` instead of just `Subcategory`
- Useful for maintaining complex taxonomy structures

**Manual Cleanup (Alternative)**
Permanently remove hierarchical fields from files using exiftool:
```bash
exiftool -HierarchicalSubject= "photo.jpg"
```

### 8. Verbose Logging

**Detailed Output Mode**
Use `-v` flag for comprehensive activity reporting:
- Files processed and their paths
- Keywords found in each file
- Success/failure status
- Error details for troubleshooting

**Summary Statistics**
- Total files scanned
- Files with keywords found
- Number of errors encountered

### 9. XMP Sidecar Support

**Automatic Sidecar Detection**
- Recognizes `.xmp` sidecar files
- Automatically applies keywords to associated media files
- Handles cases where main file has no embedded metadata
- Common in professional photography workflows

### 10. Safety Features

**Non-Destructive Operation**
- Never modifies original image files or embedded XMP data
- Only adds/modifies macOS extended attributes (Finder tags)
- Original keywords remain in files unchanged

**Dry Run Preview**
- Test operations without making changes
- See exactly what will happen before committing
- Verify keyword extraction accuracy

**Error Handling**
- Continues processing remaining files if errors occur
- Reports errors without crashing
- Validates file paths and permissions
- Checks for required dependencies (exiftool, fswatch)

### 11. Integration Features

**Spotlight Search Integration**
- Keywords become Finder tags automatically indexed by Spotlight
- Search for images across your system using keyword tags
- Works with macOS Finder's tag filtering

**Adobe Bridge Workflow**
- Add/modify keywords in Adobe Bridge
- Background service automatically detects changes
- Finder tags update within seconds
- Seamless integration with creative workflows

**fswatch-Based Monitoring**
- Uses macOS-native FSEvents for reliable file monitoring
- Efficient CPU usage
- Scales to large directory structures
- Detects changes across volumes

## Technical Specifications

**Dependencies**
- Python 3 (Anaconda or system Python at `/opt/anaconda3/bin/python3`)
- exiftool - XMP metadata extraction
- fswatch - File system monitoring
- rumps - Menu bar functionality
- tkinter - GUI dashboard (included with Python)

**Platform**
- macOS only (uses Finder tags, launchd, and macOS APIs)
- Tested on modern macOS versions

**Performance**
- Processes files in seconds
- Minimal CPU overhead in watch mode
- Efficient recursive directory traversal
- Handles large photo libraries
- Non-blocking UI operations (threaded)

**Architecture**
- Native macOS app bundle (96KB)
- Three integrated Python applications:
  - Menu bar app (bridge_menubar.py)
  - GUI dashboard (bridge_dashboard_gui.py)
  - Core engine (bridge_keywords_to_tags.py)
- Modular function design
- Configuration via script variables or GUI
- Service management via launchd plists
- Singleton instance protection with file locking

**App Bundle Structure**
```
Bridge Keywords to Tags.app/
├── Contents/
│   ├── Info.plist              # App metadata
│   ├── MacOS/
│   │   └── Bridge Keywords to Tags  # Launcher script
│   └── Resources/
│       ├── bridge_menubar.py
│       ├── bridge_dashboard_gui.py
│       └── bridge_keywords_to_tags.py
```

**External Dependencies** (must be installed):
- exiftool (via Homebrew)
- fswatch (via Homebrew)
- rumps Python package

## Use Cases

**Professional Photographers**
- Sync Adobe Bridge keywords to macOS for system-wide search
- Monitor import directories for automatic tagging
- Keep Finder tags synchronized with metadata changes

**Digital Asset Management**
- Batch tag large photo libraries
- Maintain consistency between applications
- Enable Spotlight search for archived projects

**Photo Organization**
- Convert existing XMP keywords to Finder tags
- Organize files using macOS tag colors
- Create Smart Folders based on keywords

**Automated Workflows**
- Background service eliminates manual syncing
- Set-and-forget monitoring of active directories
- Integrate with other automation tools

**File Auditing**
- Verify keyword metadata across files
- Identify files with missing keywords
- Check for hierarchical keyword issues
- Ensure metadata consistency

## Future-Proof Design

**Extensible Configuration**
- Easy to add new file formats to `SUPPORTED_EXTENSIONS`
- Configurable watch directories without code changes
- Toggle merge/replace behavior globally or per-run

**Maintainable Code**
- Clear function separation
- Comprehensive comments
- Standard Python practices
- Error handling throughout

**Standards Compliant**
- Uses standard XMP metadata fields
- Compatible with Adobe XMP specification
- Works with industry-standard tools
