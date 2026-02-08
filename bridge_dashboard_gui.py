#!/usr/bin/env python3
"""
Bridge Keywords to Tags - GUI Dashboard

A modern GUI dashboard for monitoring and managing the keyword synchronization service.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import threading
import time

# Import from the main script
import bridge_keywords_to_tags as bkt


class BridgeDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Bridge Keywords to Tags - Dashboard")
        
        # Set larger size and center on screen
        window_width = 800
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Force window to show and come to front
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('aqua')  # Use native macOS style
        
        # Create main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bridge Keywords to Tags", 
                                font=('Helvetica', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Checking...", 
                                       font=('Helvetica', 12))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.config_text = tk.Text(config_frame, height=6, width=60, 
                                    font=('Monaco', 10), relief=tk.FLAT, 
                                    background='#ffffff', foreground='#000000')
        self.config_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.config_text.config(state=tk.DISABLED)
        
        # Watched Directories management frame
        dirs_frame = ttk.LabelFrame(main_frame, text="Watched Directories", padding="10")
        dirs_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Listbox for directories
        self.dirs_listbox = tk.Listbox(dirs_frame, height=4, font=('Monaco', 10))
        self.dirs_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        dirs_frame.columnconfigure(0, weight=1)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(dirs_frame, orient=tk.VERTICAL, command=self.dirs_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.dirs_listbox.config(yscrollcommand=scrollbar.set)
        
        # Add/Remove buttons
        dir_buttons = ttk.Frame(dirs_frame)
        dir_buttons.grid(row=0, column=2, padx=(5, 0))
        ttk.Button(dir_buttons, text="+", command=self.add_directory, width=3).grid(row=0, column=0, pady=2)
        ttk.Button(dir_buttons, text="−", command=self.remove_directory, width=3).grid(row=1, column=0, pady=2)
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="Start Service", 
                                     command=self.start_service, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Service", 
                                    command=self.stop_service, width=15)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.restart_btn = ttk.Button(button_frame, text="Restart Service", 
                                       command=self.restart_service, width=15)
        self.restart_btn.grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="Refresh", 
                   command=self.refresh_status, width=15).grid(row=0, column=3, padx=5)
        
        # Logs frame
        logs_frame = ttk.LabelFrame(main_frame, text="Recent Logs", padding="10")
        logs_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=15, 
                                                   font=('Monaco', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Start auto-refresh
        self.refresh_status()
        self.auto_refresh()
    
    def update_status_display(self, status):
        """Update the status display."""
        if status == 'running':
            status_text = "🟢 Running"
            status_color = 'green'
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
        elif status == 'stopped':
            status_text = "⚪ Stopped (installed)"
            status_color = 'orange'
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
        elif status == 'not-installed':
            status_text = "⚫ Not installed"
            status_color = 'red'
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
        else:
            status_text = "❓ Unknown"
            status_color = 'gray'
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
        
        self.status_label.config(text=status_text, foreground=status_color)
    
    def update_config_display(self):
        """Update the configuration display."""
        watch_paths = bkt.get_configured_watch_paths()
        
        config_text = f"Strip prefixes: {'Yes' if bkt.STRIP_HIERARCHICAL_PREFIXES else 'No'}\n"
        config_text += f"Replace mode: {'Yes' if bkt.WATCH_REPLACE_MODE else 'No (merge)'}\n"
        config_text += f"Marker keyword: {'sync' if bkt.MARKER_KEYWORD else 'None (all files)'}"
        
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, config_text)
        self.config_text.config(state=tk.DISABLED)
        
        # Update directories listbox
        self.dirs_listbox.delete(0, tk.END)
        for path in watch_paths:
            self.dirs_listbox.insert(tk.END, str(path))
    
    def load_logs(self):
        """Load recent logs."""
        log_path = Path.home() / "Library" / "Logs" / "bridge-keywords-watcher.log"
        
        if not log_path.exists():
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, "No logs available. Service hasn't been started yet.")
            return
        
        try:
            # Read last 100 lines
            result = subprocess.run(['tail', '-100', str(log_path)], 
                                    capture_output=True, text=True, timeout=2)
            
            self.log_text.delete(1.0, tk.END)
            if result.stdout:
                self.log_text.insert(1.0, result.stdout)
                self.log_text.see(tk.END)  # Scroll to bottom
            else:
                self.log_text.insert(1.0, "Log file is empty.")
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, f"Error loading logs: {str(e)}")
    
    def refresh_status(self):
        """Refresh all status information."""
        def refresh_thread():
            try:
                status = bkt.service_status()
                self.root.after(0, lambda: self.update_status_display(status))
                self.root.after(0, self.update_config_display)
                self.root.after(0, self.load_logs)
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}"))
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def start_service(self):
        """Start the service."""
        def start_thread():
            try:
                script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
                
                # Install if needed
                if bkt.service_status() == 'not-installed':
                    bkt.service_install(script_path, autostart=False)
                
                if bkt.service_start():
                    self.root.after(0, lambda: self.status_bar.config(
                        text="Service started successfully"))
                    self.root.after(1000, self.refresh_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"))
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_service(self):
        """Stop the service."""
        def stop_thread():
            try:
                if bkt.service_stop():
                    self.root.after(0, lambda: self.status_bar.config(
                        text="Service stopped successfully"))
                    self.root.after(1000, self.refresh_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"))
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def restart_service(self):
        """Restart the service."""
        def restart_thread():
            try:
                if bkt.service_restart():
                    self.root.after(0, lambda: self.status_bar.config(
                        text="Service restarted successfully"))
                    self.root.after(2000, self.refresh_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"Error: {str(e)}"))
        
        threading.Thread(target=restart_thread, daemon=True).start()
    
    def auto_refresh(self):
        """Auto-refresh every 10 seconds."""
        self.refresh_status()
        self.root.after(10000, self.auto_refresh)
    
    def add_directory(self):
        """Add a directory using native macOS folder picker."""
        def add_async():
            try:
                print("[DEBUG] Starting add_directory")
                # Use AppleScript to show folder picker and return POSIX path directly
                applescript = '''
                tell application "System Events"
                    activate
                    set selectedFolder to choose folder with prompt "Select a folder to watch:"
                    return POSIX path of selectedFolder
                end tell
                '''
                print("[DEBUG] Running AppleScript...")
                result = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                print(f"[DEBUG] AppleScript return code: {result.returncode}")
                print(f"[DEBUG] AppleScript stdout: {result.stdout}")
                print(f"[DEBUG] AppleScript stderr: {result.stderr}")
                
                if result.returncode != 0:
                    print("[DEBUG] User cancelled or error")
                    self.root.after(0, lambda: self.status_bar.config(text="Folder selection cancelled"))
                    return  # User cancelled
                
                # Get POSIX path directly from AppleScript
                posix_path = result.stdout.strip()
                print(f"[DEBUG] POSIX path: {posix_path}")
                
                if not posix_path:
                    print("[DEBUG] Empty path!")
                    self.root.after(0, lambda: self.status_bar.config(text="Error: Could not get folder path"))
                    return
                
                # Read current config
                print("[DEBUG] Reading config file...")
                script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
                with open(script_path, 'r') as f:
                    content = f.read()
                
                # Find WATCH_DIRECTORIES and add new path
                print("[DEBUG] Searching for WATCH_DIRECTORIES...")
                import re
                match = re.search(r'WATCH_DIRECTORIES = \[(.*?)\]', content, re.DOTALL)
                if match:
                    print("[DEBUG] Found WATCH_DIRECTORIES")
                    dirs_content = match.group(1)
                    # Add new directory
                    new_line = f'    "{posix_path}",\n'
                    if dirs_content.strip():
                        new_dirs = dirs_content.rstrip() + '\n' + new_line
                    else:
                        new_dirs = '\n' + new_line
                    
                    print(f"[DEBUG] New dirs content: {new_dirs[:100]}...")
                    
                    new_content = content.replace(
                        f'WATCH_DIRECTORIES = [{dirs_content}]',
                        f'WATCH_DIRECTORIES = [{new_dirs}]'
                    )
                    
                    print("[DEBUG] Writing to file...")
                    with open(script_path, 'w') as f:
                        f.write(new_content)
                    print("[DEBUG] File written successfully!")
                    
                    self.root.after(0, lambda: self.status_bar.config(text=f"Added: {posix_path}"))
                    self.root.after(0, self.refresh_status)
                    
                    # Reload the module
                    print("[DEBUG] Reloading module...")
                    import importlib
                    importlib.reload(bkt)
                    print("[DEBUG] Module reloaded!")
                else:
                    print("[DEBUG] WATCH_DIRECTORIES not found in file!")
                    self.root.after(0, lambda: self.status_bar.config(text="Error: Could not find WATCH_DIRECTORIES"))
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(text=f"Error: {str(e)}"))
        
        threading.Thread(target=add_async, daemon=True).start()
    
    def remove_directory(self):
        """Remove selected directory."""
        selection = self.dirs_listbox.curselection()
        if not selection:
            self.status_bar.config(text="Please select a directory to remove")
            return
        
        def remove_async():
            try:
                selected_path = self.dirs_listbox.get(selection[0])
                
                # Read current config
                script_path = Path(__file__).parent / "bridge_keywords_to_tags.py"
                with open(script_path, 'r') as f:
                    content = f.read()
                
                # Remove the line containing this path
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if selected_path not in line or 'WATCH_DIRECTORIES' in line:
                        new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                
                with open(script_path, 'w') as f:
                    f.write(new_content)
                
                self.root.after(0, lambda: self.status_bar.config(text=f"Removed: {selected_path}"))
                self.root.after(0, self.refresh_status)
                
                # Reload the module
                import importlib
                importlib.reload(bkt)
            except Exception as e:
                self.root.after(0, lambda: self.status_bar.config(text=f"Error: {str(e)}"))
        
        threading.Thread(target=remove_async, daemon=True).start()


def main():
    # Check if running on macOS
    if sys.platform != 'darwin':
        print("Error: This dashboard only works on macOS")
        sys.exit(1)
    
    root = tk.Tk()
    app = BridgeDashboard(root)
    root.mainloop()


if __name__ == '__main__':
    main()
