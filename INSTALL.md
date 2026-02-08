# Installation Guide: Bridge Keywords to Tags

This guide will help you install and set up the **Bridge Keywords to Tags** application on your macOS computer.

## System Requirements

- **macOS**: 10.14 (Mojave) or later
- **Python 3**: Pre-installed or via Homebrew/Anaconda
- **Homebrew**: For installing dependencies

## Installation Steps

### 1. Install Homebrew (if not already installed)

Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions to complete the installation.

### 2. Install Required Dependencies

Install `exiftool` and `fswatch` using Homebrew:

```bash
brew install exiftool fswatch
```

**What these do:**
- `exiftool`: Reads XMP metadata and keywords from your image files
- `fswatch`: Monitors directories for file changes in real-time

### 3. Install Python Dependencies

Install the required Python package `rumps` (for the menu bar interface):

```bash
pip3 install rumps
```

**Note:** `tkinter` (for the dashboard GUI) is usually included with Python. If you get errors about tkinter not being available, you may need to reinstall Python with tkinter support.

### 4. Copy the Application

Copy the `Bridge Keywords to Tags.app` to your **Applications** folder:

```bash
cp -R "Bridge Keywords to Tags.app" /Applications/
```

Alternatively, you can drag and drop the app from Finder into your Applications folder.

### 5. Configure Python Path (if needed)

The app is configured to use Python at `/opt/anaconda3/bin/python3`. If your Python is installed elsewhere, you'll need to update the launcher script:

1. Right-click on `Bridge Keywords to Tags.app` in Applications
2. Select **Show Package Contents**
3. Navigate to `Contents/MacOS/`
4. Edit the `Bridge Keywords to Tags` file with a text editor
5. Update the `PYTHON_PATH` variable to point to your Python 3 installation

To find your Python path, run in Terminal:

```bash
which python3
```

### 6. Grant Permissions

When you first launch the app, macOS may ask for various permissions:

1. **Accessibility Access**: Required for the menu bar functionality
2. **Full Disk Access**: Required to read/write XMP metadata and Finder tags
3. **File System Access**: Required to monitor watched directories

To grant these manually:

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access** and add `Bridge Keywords to Tags.app`
3. Select **Accessibility** and add `Bridge Keywords to Tags.app`

### 7. Launch the Application

Double-click `Bridge Keywords to Tags.app` in your Applications folder.

You should see a bridge icon appear in your menu bar at the top of the screen.

## Initial Configuration

### Set Up Your First Watch Directory

1. Click the bridge icon in the menu bar
2. Select **Dashboard** to open the configuration interface
3. Click the **+** button next to "Watched Directories"
4. Browse to the folder containing your Adobe Bridge files
5. Click **Choose** to add it to the watch list
6. Click **Start Service** to begin monitoring

### Configure Sync Settings

Edit the configuration file to customize behavior:

1. Click the bridge icon → **Open Configuration**
2. Modify these settings in `bridge_keywords_to_tags.py`:

```python
# Process only files with 'sync' keyword, or set to None to process all files
MARKER_KEYWORD = "sync"  

# Remove hierarchical prefixes (e.g., "Nature/Wildlife" → "Wildlife")
STRIP_HIERARCHICAL_PREFIXES = True  

# Replace tags (True) or merge with existing tags (False)
# True = Finder tags will exactly match Bridge keywords (recommended)
# False = New keywords will be added to existing Finder tags
WATCH_REPLACE_MODE = True  
```

3. Save the file
4. Restart the service from the menu bar

### Enable Auto-Start (Optional)

To have the menu bar app launch automatically at login:

1. Click the bridge icon in the menu bar
2. Click **Automatically open** to enable the checkmark (✓)

The app will now start automatically when you log in to your Mac.

## Verifying Installation

### Test the Service

1. Open the Dashboard from the menu bar
2. Check that **Service Status** shows as "Running" (green)
3. View the logs section to see activity
4. Add a test image with keywords to one of your watched directories
5. Check if the Finder tags appear on the file (right-click → **Get Info**)

### Check Logs

To view detailed logs:

1. Click the bridge icon → **View Logs**
2. Or check the log file directly:

```bash
cat ~/Library/Logs/bridge_keywords_sync.log
```

## Troubleshooting

### App Won't Launch

**Issue**: Double-clicking does nothing or shows an error

**Solutions**:
- Right-click the app → **Open** (bypasses Gatekeeper on first launch)
- Check that Python path is correct (see Step 5)
- Verify permissions are granted (see Step 6)

### Service Won't Start

**Issue**: Dashboard shows "Stopped" status

**Solutions**:
```bash
# Check if launchd service is loaded
launchctl list | grep bridge-keywords

# Manually load the service
launchctl load ~/Library/LaunchAgents/com.user.bridge-keywords-watcher.plist

# Check for errors in system logs
tail -f ~/Library/Logs/bridge_keywords_sync.log
```

### Keywords Not Syncing

**Issue**: Tags don't appear on files

**Solutions**:
- Verify `exiftool` is installed: `which exiftool`
- Check if files have keywords: `exiftool -Keywords /path/to/file.jpg`
- If using marker keyword mode, ensure files have the marker keyword
- Check logs for errors
- Verify watched directory is correct in Dashboard

### Dashboard Won't Open

**Issue**: Clicking Dashboard does nothing

**Solutions**:
- Check if Python has tkinter support: `python3 -m tkinter`
- Try launching from Terminal to see errors:
  ```bash
  /opt/anaconda3/bin/python3 "/Applications/Bridge Keywords to Tags.app/Contents/Resources/bridge_dashboard_gui.py"
  ```

### Permission Errors

**Issue**: "Permission denied" or "Operation not permitted"

**Solutions**:
- Grant Full Disk Access (see Step 6)
- Check file permissions on watched directories
- Ensure you have read/write access to the files

## Uninstallation

To completely remove the application:

1. **Stop the service:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.bridge-keywords-watcher.plist
   ```

2. **Remove the launch agent:**
   ```bash
   rm ~/Library/LaunchAgents/com.user.bridge-keywords-watcher.plist
   ```

3. **Delete the application:**
   ```bash
   rm -rf "/Applications/Bridge Keywords to Tags.app"
   ```

4. **Remove logs and configuration** (optional):
   ```bash
   rm ~/Library/Logs/bridge_keywords_sync.log
   rm /tmp/bridge_menubar.lock
   ```

## Getting Help

- Check the logs: `~/Library/Logs/bridge_keywords_sync.log`
- Review the README: Open `README.md` in the app folder
- Check tutorials: `TUTORIAL_Building_Bridge_App.md` for understanding how it works

## Next Steps

- Read `FEATURES.md` for complete feature documentation
- See `TUTORIAL_Building_Bridge_App.md` to learn how the app was built
- Customize the configuration file for your workflow
- Add multiple watched directories as needed

---

**Installation complete!** The Bridge Keywords to Tags app is now ready to automatically sync your Adobe Bridge keywords to macOS Finder tags.
