# Tutorial: Creating a macOS App Bundle from Python Scripts

This tutorial teaches you how to create a native macOS `.app` bundle that launches Python scripts, complete with a custom icon. No complex tools required—just the built-in macOS utilities and a text editor.

## Table of Contents
1. [Understanding macOS App Bundles](#understanding-macos-app-bundles)
2. [Creating the App Structure](#creating-the-app-structure)
3. [Writing the Info.plist](#writing-the-infoplist)
4. [Creating the Launcher Script](#creating-the-launcher-script)
5. [Adding Your Python Scripts](#adding-your-python-scripts)
6. [Adding a Custom Icon](#adding-a-custom-icon)
7. [Testing and Troubleshooting](#testing-and-troubleshooting)
8. [Advanced Concepts](#advanced-concepts)

---

## Understanding macOS App Bundles

### What is a .app bundle?

A `.app` file in macOS is actually a **directory** (folder) with a special structure that macOS recognizes as an application. It's called a "bundle" because it bundles all the app's resources together.

### Why create an app bundle?

- **User-friendly**: Double-click to launch instead of using Terminal
- **Finder integration**: Shows in Applications folder with an icon
- **Professional**: Looks and behaves like a native macOS app
- **Login items**: Can be added to auto-start on login

### Basic Bundle Structure

```
YourApp.app/
├── Contents/
│   ├── Info.plist           # App metadata (required)
│   ├── MacOS/               # Executable files go here
│   │   └── YourAppName      # The launcher script
│   └── Resources/           # App resources (icons, scripts, etc.)
│       ├── AppIcon.icns     # App icon (optional)
│       └── your_script.py   # Your Python scripts
```

**Key Points:**
- The `.app` extension is what makes macOS recognize it as an application
- `Info.plist` tells macOS about your app (name, version, what to run)
- `MacOS/` contains the executable that macOS launches
- `Resources/` stores everything else your app needs

---

## Creating the App Structure

### Step 1: Create the Directory Structure

Open Terminal and run:

```bash
# Navigate to where you want to create your app
cd ~/Desktop

# Create the bundle structure
mkdir -p "My Python App.app/Contents/"{MacOS,Resources}
```

**Explanation:**
- `mkdir -p` creates directories and any parent directories needed
- `"My Python App.app"` - The quotes handle spaces in the name
- `/Contents/"{MacOS,Resources}` - Creates both directories at once (bash brace expansion)

**Result:**
```
My Python App.app/
└── Contents/
    ├── MacOS/
    └── Resources/
```

### Step 2: Verify the Structure

```bash
# List the structure to verify
ls -R "My Python App.app"
```

You should see:
```
My Python App.app/Contents:
MacOS     Resources

My Python App.app/Contents/MacOS:

My Python App.app/Contents/Resources:
```

---

## Writing the Info.plist

### What is Info.plist?

`Info.plist` is an XML file that contains metadata about your app. macOS reads this file to learn:
- What the app is called
- Which file to execute when launched
- Where the app icon is
- Which macOS version is required
- Whether to show the app in the Dock

### Step 3: Create Info.plist

Create the file:

```bash
nano "My Python App.app/Contents/Info.plist"
```

**Or use any text editor:**
```bash
open -e "My Python App.app/Contents/Info.plist"
```

### Step 4: Add the XML Content

Paste this template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>My Python App</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourname.mypythonapp</string>
    <key>CFBundleName</key>
    <string>My Python App</string>
    <key>CFBundleDisplayName</key>
    <string>My Python App</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
```

### Understanding Each Field

| Key | What It Does | Example Value |
|-----|-------------|---------------|
| `CFBundleExecutable` | Name of the file in MacOS/ to run | `My Python App` |
| `CFBundleIconFile` | Icon filename (without .icns) | `AppIcon` |
| `CFBundleIdentifier` | Unique reverse-DNS identifier | `com.yourname.mypythonapp` |
| `CFBundleName` | Internal name | `My Python App` |
| `CFBundleDisplayName` | Name shown to users | `My Python App` |
| `CFBundlePackageType` | Must be `APPL` for applications | `APPL` |
| `CFBundleShortVersionString` | User-facing version | `1.0.0` |
| `CFBundleVersion` | Build number | `1` |
| `LSMinimumSystemVersion` | Minimum macOS version | `10.13` (High Sierra) |
| `LSUIElement` | Hide from Dock? | `false` (show) / `true` (hide) |
| `NSHighResolutionCapable` | Support Retina displays? | `true` |

**Important:**
- `CFBundleExecutable` must match the filename you create in MacOS/ (without extension)
- `CFBundleIdentifier` should be unique (use your name/domain reversed)
- Set `LSUIElement` to `true` for menu bar apps that shouldn't show in Dock

---

## Creating the Launcher Script

### What is the Launcher Script?

The launcher script is a shell script (bash/zsh) that macOS executes when you double-click the app. It's responsible for:
1. Finding your Python scripts
2. Setting up the environment
3. Running Python with the correct arguments

### Step 5: Create the Launcher

Create the file (name must match `CFBundleExecutable` from Info.plist):

```bash
nano "My Python App.app/Contents/MacOS/My Python App"
```

### Step 6: Write the Launcher Script

**Simple Version** (if Python is at a known location):

```bash
#!/bin/bash

# Get the directory containing this script
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$APP_DIR/../Resources"

# Change to Resources directory
cd "$RESOURCES_DIR"

# Launch the Python script
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py"
```

**Advanced Version** (with error logging):

```bash
#!/bin/bash

# Log file for debugging
LOG_FILE="$HOME/my_app_launch.log"
echo "[$(date)] Starting My Python App" > "$LOG_FILE"

# Get directories
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$APP_DIR/../Resources"

echo "[$(date)] APP_DIR: $APP_DIR" >> "$LOG_FILE"
echo "[$(date)] RESOURCES_DIR: $RESOURCES_DIR" >> "$LOG_FILE"

# Change to Resources directory
cd "$RESOURCES_DIR" 2>> "$LOG_FILE"

echo "[$(date)] Current directory: $(pwd)" >> "$LOG_FILE"
echo "[$(date)] Launching Python..." >> "$LOG_FILE"

# Launch Python script, redirect output to log
/usr/bin/python3 "$RESOURCES_DIR/my_script.py" >> "$LOG_FILE" 2>&1
```

### Understanding the Launcher Script

**Line by line:**

```bash
#!/bin/bash
```
- **Shebang**: Tells the system this is a bash script
- Must be the first line

```bash
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
```
- `${BASH_SOURCE[0]}` - Path to this script
- `dirname` - Get the directory containing the script
- `cd ... && pwd` - Navigate there and print the full path
- Result: `/path/to/My Python App.app/Contents/MacOS`

```bash
RESOURCES_DIR="$APP_DIR/../Resources"
```
- Go up one level (`..`) then into `Resources`
- `../` means "parent directory"

```bash
cd "$RESOURCES_DIR"
```
- Change to Resources directory
- Important if your script uses relative paths

```bash
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py"
```
- `exec` - Replace the shell process with Python (cleaner)
- `/usr/bin/python3` - System Python
- Use full path to Python (can also be `/opt/anaconda3/bin/python3` for Anaconda)

### Step 7: Make the Launcher Executable

**Critical step!** The launcher must have execute permissions:

```bash
chmod +x "My Python App.app/Contents/MacOS/My Python App"
```

**Verify permissions:**
```bash
ls -l "My Python App.app/Contents/MacOS/My Python App"
```

Should show: `-rwxr-xr-x` (the `x` means executable)

---

## Adding Your Python Scripts

### Step 8: Copy Your Python Scripts

Copy your Python files to the Resources directory:

```bash
cp my_script.py "My Python App.app/Contents/Resources/"
```

**For multiple files:**
```bash
cp script1.py script2.py script3.py "My Python App.app/Contents/Resources/"
```

### Important Considerations

**Python Path:**
If your script imports other modules you've written, make sure they're all in Resources:

```python
# In your main script
import sys
from pathlib import Path

# Add Resources directory to Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Now you can import your other modules
import my_other_module
```

**Dependencies:**
Your app relies on:
- The Python version at the path you specified
- All installed packages (pip/conda)
- External tools (if any)

These must already be installed on the system where the app runs.

---

## Adding a Custom Icon

### Understanding Icon Formats

macOS uses `.icns` files for app icons. These files contain multiple sizes of the same image (for different contexts).

**Required sizes:**
- 16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024
- Each size needs a standard and @2x (Retina) version

### Step 9: Create an Icon Set

Starting with a square image (PNG or JPG, at least 1024x1024):

```bash
# Create iconset directory
mkdir MyAppIcon.iconset

# Convert source image to all required sizes
sips -s format png -z 16 16     icon.png --out MyAppIcon.iconset/icon_16x16.png
sips -s format png -z 32 32     icon.png --out MyAppIcon.iconset/icon_16x16@2x.png
sips -s format png -z 32 32     icon.png --out MyAppIcon.iconset/icon_32x32.png
sips -s format png -z 64 64     icon.png --out MyAppIcon.iconset/icon_32x32@2x.png
sips -s format png -z 128 128   icon.png --out MyAppIcon.iconset/icon_128x128.png
sips -s format png -z 256 256   icon.png --out MyAppIcon.iconset/icon_128x128@2x.png
sips -s format png -z 256 256   icon.png --out MyAppIcon.iconset/icon_256x256.png
sips -s format png -z 512 512   icon.png --out MyAppIcon.iconset/icon_256x256@2x.png
sips -s format png -z 512 512   icon.png --out MyAppIcon.iconset/icon_512x512.png
sips -s format png -z 1024 1024 icon.png --out MyAppIcon.iconset/icon_512x512@2x.png
```

**What `sips` does:**
- `sips` - Scriptable Image Processing System (built into macOS)
- `-s format png` - Convert to PNG format
- `-z HEIGHT WIDTH` - Resize to specified dimensions
- `--out` - Output file path

### Step 10: Convert to .icns

```bash
# Convert iconset to icns file
iconutil -c icns MyAppIcon.iconset -o "My Python App.app/Contents/Resources/AppIcon.icns"

# Clean up iconset folder
rm -rf MyAppIcon.iconset
```

**What `iconutil` does:**
- Built-in macOS tool for creating .icns files
- `-c icns` - Create an icns file
- `-o` - Output path

### Step 11: Reference Icon in Info.plist

Make sure your Info.plist has:

```xml
<key>CFBundleIconFile</key>
<string>AppIcon</string>
```

**Note:** Use the filename without `.icns` extension!

### Step 12: Refresh the Icon Cache

```bash
# Update the bundle's timestamp
touch "My Python App.app"

# Restart Finder (or Dock) to see the new icon
killall Finder
# or
killall Dock
```

---

## Testing and Troubleshooting

### Testing Your App

**Test 1: Run the launcher directly**
```bash
"My Python App.app/Contents/MacOS/My Python App"
```

If this works, the launcher script is correct.

**Test 2: Use the `open` command**
```bash
open "My Python App.app"
```

This simulates double-clicking in Finder.

**Test 3: Double-click in Finder**
Navigate to the app in Finder and double-click it.

### Common Problems and Solutions

#### Problem: "Permission denied"

**Cause:** Launcher script not executable

**Solution:**
```bash
chmod +x "My Python App.app/Contents/MacOS/My Python App"
```

#### Problem: App opens but nothing happens

**Cause:** Python path is wrong or script has errors

**Solution 1:** Check Python path
```bash
which python3
# Use this path in your launcher
```

**Solution 2:** Add logging to see what's happening
```bash
#!/bin/bash
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py" > "$HOME/app_output.log" 2>&1
```

Then check `~/app_output.log` for errors.

#### Problem: "ModuleNotFoundError"

**Cause:** Python packages not installed

**Solution:** Install required packages:
```bash
pip3 install package_name --user
```

Or use a specific Python (like Anaconda) that has the packages:
```bash
exec /opt/anaconda3/bin/python3 "$RESOURCES_DIR/my_script.py"
```

#### Problem: Icon doesn't show

**Cause:** Icon not properly created or referenced

**Solution 1:** Verify icon exists
```bash
ls -lh "My Python App.app/Contents/Resources/AppIcon.icns"
```

**Solution 2:** Check Info.plist has icon reference

**Solution 3:** Refresh icon cache
```bash
touch "My Python App.app"
killall Finder
```

#### Problem: App won't open - "Damaged or incomplete"

**Cause:** Missing Info.plist or incorrect structure

**Solution:** Verify all required files exist:
```bash
ls -R "My Python App.app/Contents/"
```

Should show:
- `Info.plist`
- `MacOS/My Python App` (executable)
- `Resources/` (your scripts)

---

## Advanced Concepts

### Making Apps Portable

**Current limitation:** Your app depends on:
- System Python at specific path
- Installed Python packages
- External tools

**To make truly portable:**
Use `py2app` (creates standalone app with bundled Python):
```bash
pip install py2app
py2applet --make-setup my_script.py
python setup.py py2app
```

This creates a ~50-100MB app with everything included.

### Menu Bar Apps (LSUIElement)

For apps that live in the menu bar (like our Bridge app):

In Info.plist, set:
```xml
<key>LSUIElement</key>
<true/>
```

This makes the app:
- Not show in the Dock
- Not appear in Cmd+Tab switcher
- Only show the menu bar icon

### Auto-Start at Login

**Two methods:**

**Method 1: Login Items (manual)**
1. System Settings → General → Login Items
2. Click `+` and select your app

**Method 2: LaunchAgent (programmatic)**

Create a plist file at:
```
~/Library/LaunchAgents/com.yourname.myapp.plist
```

Content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourname.myapp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>/path/to/My Python App.app</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.yourname.myapp.plist
```

### Code Signing (Advanced)

For distribution outside the App Store:

```bash
# Sign the app
codesign --force --deep --sign - "My Python App.app"
```

For proper signing (requires Apple Developer account):
```bash
codesign --force --deep --sign "Developer ID Application: Your Name" "My Python App.app"
```

### Handling Arguments

If your script needs arguments, modify the launcher:

```bash
# Pass all arguments to the Python script
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py" "$@"
```

Or set fixed arguments:
```bash
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py" --mode=gui --verbose
```

### Using Environment Variables

Set environment variables in the launcher:

```bash
#!/bin/bash

# Set environment variables
export MY_APP_MODE="production"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Then run Python
exec /usr/bin/python3 "$RESOURCES_DIR/my_script.py"
```

---

## Summary: Complete Checklist

When creating a new app, follow these steps:

- [ ] Create directory structure: `.app/Contents/{MacOS,Resources}`
- [ ] Write `Info.plist` with correct metadata
- [ ] Create launcher script in `MacOS/`
- [ ] Make launcher executable (`chmod +x`)
- [ ] Copy Python scripts to `Resources/`
- [ ] (Optional) Create and add icon
- [ ] Test with `open` command
- [ ] Test by double-clicking in Finder
- [ ] Check logs if something goes wrong

## Quick Reference Commands

```bash
# Create structure
mkdir -p "App.app/Contents/"{MacOS,Resources}

# Make executable
chmod +x "App.app/Contents/MacOS/AppName"

# Test
open "App.app"

# Refresh icon
touch "App.app" && killall Finder

# View structure
ls -R "App.app/Contents"

# Check logs
tail -f ~/app_launch.log
```

---

## Resources

**Apple Documentation:**
- [Bundle Programming Guide](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/Introduction/Introduction.html)
- [Info.plist Keys](https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Introduction/Introduction.html)

**Tools:**
- `sips` - man sips (in Terminal)
- `iconutil` - man iconutil
- `py2app` - https://py2app.readthedocs.io/

**Tips:**
- Keep your app simple - complexity = more things that can break
- Test on a fresh Mac (or new user account) to catch missing dependencies
- Use version control (git) to track changes to your app structure
- Document any external dependencies in a README

---

## Example: Complete Minimal App

Here's everything for a minimal working app:

```bash
# Create structure
cd ~/Desktop
mkdir -p "Hello.app/Contents/"{MacOS,Resources}

# Create Python script
cat > "Hello.app/Contents/Resources/hello.py" << 'EOF'
#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()
messagebox.showinfo("Hello", "Hello from my Python app!")
root.destroy()
EOF

# Create Info.plist
cat > "Hello.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Hello</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.hello</string>
    <key>CFBundleName</key>
    <string>Hello</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF

# Create launcher
cat > "Hello.app/Contents/MacOS/Hello" << 'EOF'
#!/bin/bash
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$APP_DIR/../Resources"
exec /usr/bin/python3 "$RESOURCES_DIR/hello.py"
EOF

# Make executable
chmod +x "Hello.app/Contents/MacOS/Hello"

# Test
open "Hello.app"
```

**Result:** A dialog box saying "Hello from my Python app!"

---

You now know everything needed to create macOS app bundles from Python scripts! 

**Next steps:**
1. Try creating the simple Hello.app example above
2. Modify it to run your own script
3. Add an icon
4. Experiment with Info.plist settings

Good luck building your apps!
