#!/usr/bin/env python3
"""
Bridge Keywords to Tags - Menu Bar App

A macOS menu bar application for managing the keyword synchronization service.
"""

import rumps
import subprocess
import sys
import threading
import os
import fcntl
import time
from pathlib import Path
from datetime import datetime

# Import from the main script
import bridge_keywords_to_tags as bkt

class BridgeMenuBarApp(rumps.App):
    def __init__(self):
        print("Initializing BridgeMenuBarApp...")
        super(BridgeMenuBarApp, self).__init__(
            "Bridge",  # More visible text
            icon=None,
            quit_button=None
        )
        print("rumps.App initialized")
        
        # Track service state
        self.is_running = False
        self.last_check = None
        self.auto_start_enabled = self.check_auto_start()
        print("State variables initialized")
        
        # Build menu
        print("Building menu...")
        # Set initial marker status
        marker_text = "sync enabled" if bkt.MARKER_KEYWORD else "all enabled"
        auto_start_text = "Automatically open ✓" if self.auto_start_enabled else "Automatically open"
        self.menu = [
            rumps.MenuItem("Service Status", callback=self.show_status),
            rumps.MenuItem("Show Config", callback=self.show_config),
            rumps.MenuItem(marker_text, callback=self.show_marker_status),
            None,  # Separator
            rumps.MenuItem("Start Service", callback=self.start_service),
            rumps.MenuItem("Stop Service", callback=self.stop_service),
            rumps.MenuItem("Restart Service", callback=self.restart_service),
            None,  # Separator
            rumps.MenuItem("View Logs", callback=self.view_logs),
            rumps.MenuItem("Open Configuration", callback=self.open_config),
            rumps.MenuItem("Dashboard", callback=self.open_dashboard),
            None,  # Separator
            rumps.MenuItem("Process Current Directory", callback=self.process_current),
            rumps.MenuItem("Stop Processing", callback=self.stop_processing),
            rumps.MenuItem(auto_start_text, callback=self.toggle_auto_start),
            None,  # Separator
            rumps.MenuItem("About", callback=self.show_about),
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
        print("Menu built")
        
        # Start status update timer
        print("Starting timer...")
        self.timer = rumps.Timer(self.update_status, 5)
        self.timer.start()
        print("Timer started")
        
        # Initial status check
        print("Doing initial status check...")
        self.update_status(None)
        print("Initialization complete!")
    
    def update_status(self, _):
        """Update service status periodically."""
        status = bkt.service_status()
        
        if status == 'running':
            self.is_running = True
            self.title = "Bridge ✓"
            self.menu["Start Service"].set_callback(None)  # Disable
            self.menu["Stop Service"].set_callback(self.stop_service)  # Enable
            self.menu["Restart Service"].set_callback(self.restart_service)  # Enable
        elif status == 'stopped':
            self.is_running = False
            self.title = "Bridge ○"
            self.menu["Start Service"].set_callback(self.start_service)  # Enable
            self.menu["Stop Service"].set_callback(None)  # Disable
            self.menu["Restart Service"].set_callback(None)  # Disable
        else:  # not-installed or unknown
            self.is_running = False
            self.title = "Bridge"
            self.menu["Start Service"].set_callback(self.start_service)  # Enable for installation
            self.menu["Stop Service"].set_callback(None)  # Disable
            self.menu["Restart Service"].set_callback(None)  # Disable
        
        # Update marker keyword status in menu
        old_marker_text = "sync enabled" if bkt.MARKER_KEYWORD else "all enabled"
        new_marker_text = "sync enabled" if bkt.MARKER_KEYWORD else "all enabled"
        # Find and update the marker menu item
        for item in self.menu.values():
            if hasattr(item, 'title') and item.title in ["sync enabled", "all enabled"]:
                item.title = new_marker_text
                break
        
        self.last_check = datetime.now()
    
    @rumps.clicked("Service Status")
    def show_status(self, _):
        """Show detailed service status."""
        def show_status_async():
            try:
                status = bkt.service_status()
                watch_paths = bkt.get_configured_watch_paths()
                
                if status == 'running':
                    status_text = "🟢 Running"
                elif status == 'stopped':
                    status_text = "⚪ Stopped (installed)"
                elif status == 'not-installed':
                    status_text = "⚫ Not installed"
                else:
                    status_text = "❓ Unknown"
                
                subtitle = f"{len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}" if watch_paths else "No directories"
                
                rumps.notification(
                    title=f"Bridge: {status_text}",
                    subtitle=subtitle,
                    message=f"Last checked: {self.last_check.strftime('%H:%M:%S') if self.last_check else 'Never'}"
                )
            except Exception as e:
                rumps.notification(
                    title="Bridge Status Error",
                    subtitle="Failed to get status",
                    message=str(e)
                )
        
        # Run in background thread to avoid blocking UI
        thread = threading.Thread(target=show_status_async, daemon=True)
        thread.start()
    
    
    @rumps.clicked("Show Config")
    def show_config(self, _):
        """Show configuration details."""
        def show_config_async():
            try:
                watch_paths = bkt.get_configured_watch_paths()
                
                # Build configuration summary
                strip_text = f"Strip prefixes: {'Yes' if bkt.STRIP_HIERARCHICAL_PREFIXES else 'No'}"
                replace_text = f"Replace: {'Yes' if bkt.WATCH_REPLACE_MODE else 'No'}"
                marker_text = f"Marker: {'sync' if bkt.MARKER_KEYWORD else 'all'}"
                
                if not watch_paths:
                    dirs_text = "No directories"
                else:
                    dirs_list = ", ".join([p.name for p in watch_paths[:2]])
                    if len(watch_paths) > 2:
                        dirs_list += f" +{len(watch_paths) - 2} more"
                    dirs_text = f"Dirs: {dirs_list}"
                
                config_summary = f"{strip_text} | {replace_text} | {marker_text}\n{dirs_text}"
                
                rumps.notification(
                    title="Config",
                    subtitle="",
                    message=config_summary
                )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Failed to load config: {str(e)}"
                )
        
        # Run in background thread
        thread = threading.Thread(target=show_config_async, daemon=True)
        thread.start()
    
    def show_marker_status(self, sender):
        """Toggle marker keyword mode between sync and all."""
        def toggle_async():
            try:
                # Read the current config file
                script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
                with open(script_path, 'r') as f:
                    content = f.read()
                
                # Toggle the marker keyword
                if bkt.MARKER_KEYWORD is None:
                    # Switch to sync mode
                    new_content = content.replace(
                        'MARKER_KEYWORD = None',
                        'MARKER_KEYWORD = "sync"'
                    )
                    new_mode = "sync enabled"
                    message = "Only files with 'sync' keyword will be processed"
                    bkt.MARKER_KEYWORD = "sync"
                else:
                    # Switch to all mode
                    new_content = content.replace(
                        'MARKER_KEYWORD = "sync"',
                        'MARKER_KEYWORD = None'
                    )
                    new_mode = "all enabled"
                    message = "All files with XMP keywords will be processed"
                    bkt.MARKER_KEYWORD = None
                
                # Write the updated config
                with open(script_path, 'w') as f:
                    f.write(new_content)
                
                # Update menu item title
                sender.title = new_mode
                
                # Automatically restart service if it's running
                if bkt.service_status() == 'running':
                    bkt.service_restart()
                    restart_msg = " Service restarted."
                else:
                    restart_msg = ""
                
                rumps.notification(
                    title="Marker Mode Changed",
                    subtitle=new_mode,
                    message=f"{message}.{restart_msg}"
                )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Failed to toggle mode: {str(e)}"
                )
        
        # Run in background thread
        thread = threading.Thread(target=toggle_async, daemon=True)
        thread.start()
    
    @rumps.clicked("Start Service")
    def start_service(self, _):
        """Start the background service."""
        try:
            script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
            
            # Check configuration first
            watch_paths = bkt.get_configured_watch_paths()
            if not watch_paths:
                rumps.notification(
                    title="No Directories Configured",
                    subtitle="Bridge Keywords to Tags",
                    message="Edit WATCH_DIRECTORIES in the script first"
                )
                return
            
            # Install if needed
            if bkt.service_status() == 'not-installed':
                if bkt.service_install(script_path, autostart=False):
                    rumps.notification(
                        title="Service Installed",
                        subtitle="Bridge Keywords to Tags",
                        message="Service installed successfully. Starting..."
                    )
            
            # Start the service
            if bkt.service_start():
                rumps.notification(
                    title="Service Started",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Now watching {len(watch_paths)} director{'y' if len(watch_paths) == 1 else 'ies'}"
                )
                self.update_status(None)
        except Exception as e:
            rumps.notification(
                title="Error Starting Service",
                subtitle="Bridge Keywords to Tags",
                message=str(e)
            )
    
    @rumps.clicked("Stop Service")
    def stop_service(self, _):
        """Stop the background service."""
        try:
            if bkt.service_stop():
                rumps.notification(
                    title="Service Stopped",
                    subtitle="Bridge Keywords to Tags",
                    message="Service stopped successfully"
                )
                self.update_status(None)
        except Exception as e:
            rumps.notification(
                title="Error Stopping Service",
                subtitle="Bridge Keywords to Tags",
                message=str(e)
            )
    
    @rumps.clicked("Restart Service")
    def restart_service(self, _):
        """Restart the background service."""
        try:
            if bkt.service_restart():
                rumps.notification(
                    title="Service Restarted",
                    subtitle="Bridge Keywords to Tags",
                    message="Service restarted successfully"
                )
                self.update_status(None)
        except Exception as e:
            rumps.notification(
                title="Error Restarting Service",
                subtitle="Bridge Keywords to Tags",
                message=str(e)
            )
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """Open logs in Console.app."""
        log_path = Path.home() / "Library" / "Logs" / "bridge-keywords-watcher.log"
        
        if not log_path.exists():
            rumps.notification(
                title="No Logs Found",
                subtitle="Bridge Keywords to Tags",
                message="Service hasn't been started yet"
            )
            return
        
        # Open in Console.app
        subprocess.run(['open', '-a', 'Console', str(log_path)])
    
    @rumps.clicked("Open Configuration")
    def open_config(self, _):
        """Open the configuration file in default editor."""
        script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
        subprocess.run(['open', '-t', str(script_path)])
        
        rumps.notification(
            title="Configuration Opened",
            subtitle="Bridge Keywords to Tags",
            message="Edit WATCH_DIRECTORIES, then restart service"
        )
    
    @rumps.clicked("Dashboard")
    def open_dashboard(self, _):
        """Open the GUI dashboard."""
        script_path = Path(__file__).parent / "bridge_dashboard_gui.py"
        
        if not script_path.exists():
            rumps.notification(
                title="Dashboard Not Found",
                subtitle="Bridge Keywords to Tags",
                message="bridge_dashboard_gui.py not in same directory"
            )
            return
        
        # Use a simple shell command to launch and bring to front
        cmd = f'cd "{script_path.parent}" && python3 "{script_path}" & sleep 0.5 && osascript -e \'tell application "Python" to activate\' 2>/dev/null || true'
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    @rumps.clicked("Process Current Directory")
    def process_current(self, _):
        """Process the current Finder directory."""
        def process_async():
            try:
                # Get current Finder directory
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
                        subtitle="Bridge Keywords to Tags",
                        message="Could not get Finder directory"
                    )
                    return
                
                current_dir = Path(result.stdout.strip())
                
                # Run processing in background
                script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
                subprocess.Popen([
                    'python3', str(script_path), str(current_dir), '-v'
                ])
                
                rumps.notification(
                    title="Processing Started",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Processing files in {current_dir.name}"
                )
                
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Failed to process: {str(e)}"
                )
        
        # Run in background thread
        thread = threading.Thread(target=process_async, daemon=True)
        thread.start()
    
    @rumps.clicked("Stop Processing")
    def stop_processing(self, _):
        """Stop any running bridge_keywords_to_tags.py processing."""
        def stop_async():
            try:
                # Find and kill any running bridge_keywords_to_tags.py processes
                result = subprocess.run(
                    ['pgrep', '-f', 'bridge_keywords_to_tags.py'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    killed_count = 0
                    for pid in pids:
                        try:
                            subprocess.run(['kill', pid], timeout=2)
                            killed_count += 1
                        except:
                            pass
                    
                    if killed_count > 0:
                        rumps.notification(
                            title="Processing Stopped",
                            subtitle="Bridge Keywords to Tags",
                            message=f"Stopped {killed_count} processing task{'s' if killed_count > 1 else ''}"
                        )
                    else:
                        rumps.notification(
                            title="No Processes Stopped",
                            subtitle="Bridge Keywords to Tags",
                            message="Could not stop processes"
                        )
                else:
                    rumps.notification(
                        title="No Processing Running",
                        subtitle="Bridge Keywords to Tags",
                        message="No active processing tasks found"
                    )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Bridge Keywords to Tags",
                    message=f"Failed to stop processing: {str(e)}"
                )
        
        # Run in background thread
        thread = threading.Thread(target=stop_async, daemon=True)
        thread.start()
    
    def check_auto_start(self):
        """Check if app is set to auto-start."""
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.user.bridge-menubar.plist"
        return plist_path.exists()
    
    def toggle_auto_start(self, sender):
        """Toggle auto-start at login."""
        def toggle_async():
            try:
                plist_path = Path.home() / "Library" / "LaunchAgents" / "com.user.bridge-menubar.plist"
                script_path = Path(__file__).resolve()
                
                if self.auto_start_enabled:
                    # Disable auto-start
                    if plist_path.exists():
                        subprocess.run(['launchctl', 'unload', str(plist_path)], check=False)
                        plist_path.unlink()
                    self.auto_start_enabled = False
                    sender.title = "Automatically open"
                    rumps.notification(
                        title="Auto-start Disabled",
                        subtitle="Bridge Menu Bar",
                        message="App will not start automatically at login"
                    )
                else:
                    # Enable auto-start
                    plist_path.parent.mkdir(parents=True, exist_ok=True)
                    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.bridge-menubar</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
'''
                    with open(plist_path, 'w') as f:
                        f.write(plist_content)
                    
                    subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
                    self.auto_start_enabled = True
                    sender.title = "Automatically open ✓"
                    rumps.notification(
                        title="Auto-start Enabled",
                        subtitle="Bridge Menu Bar",
                        message="App will start automatically at login"
                    )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Bridge Menu Bar",
                    message=f"Failed to toggle auto-start: {str(e)}"
                )
        
        threading.Thread(target=toggle_async, daemon=True).start()
    
    @rumps.clicked("About")
    def show_about(self, _):
        """Show about notification."""
        rumps.notification(
            title="Bridge Keywords to Tags",
            subtitle="Menu Bar Application",
            message="Synchronizes Adobe Bridge/XMP keywords with macOS Finder tags"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the menu bar app."""
        rumps.quit_application()


def main():
    # Check if running on macOS
    if sys.platform != 'darwin':
        print("Error: This menu bar app only works on macOS")
        sys.exit(1)
    
    # Prevent multiple instances
    lock_file = Path('/tmp/bridge_menubar.lock')
    try:
        lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        print("Another instance is already running. Exiting.")
        sys.exit(1)
    
    # Start the app
    app = BridgeMenuBarApp()
    app.run()


if __name__ == '__main__':
    main()
