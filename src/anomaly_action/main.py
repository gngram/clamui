import gi
import os
import shutil
import sys
import argparse
from datetime import datetime

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio

class VirusPopup(Gtk.Window):
    def __init__(self, filename, virusname):
        super().__init__()
        self.filename = filename
        self.virusname = virusname
        
        self.setup_window()
        self.create_ui()
        
    def setup_window(self):
        self.set_title("Virus Detected")
        self.set_default_size(400, 250)
        self.set_modal(True)
        self.set_resizable(False)
        
        # In GTK4, windows are centered by default for modal dialogs
        # No need for set_position()
        
    def create_ui(self):
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        
        # Warning icon and title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        warning_icon.set_pixel_size(32)
        
        title_label = Gtk.Label()
        title_label.set_markup("<b>Virus Detected!</b>")
        title_label.set_halign(Gtk.Align.START)
        
        title_box.append(warning_icon)
        title_box.append(title_label)
        
        # File information
        info_frame = Gtk.Frame()
        info_frame.set_margin_top(10)
        info_frame.set_margin_bottom(10)
        
        info_grid = Gtk.Grid()
        info_grid.set_row_spacing(5)
        info_grid.set_column_spacing(10)
        info_grid.set_margin_top(10)
        info_grid.set_margin_bottom(10)
        info_grid.set_margin_start(10)
        info_grid.set_margin_end(10)
        
        # File name
        file_label = Gtk.Label()
        file_label.set_markup("<b>File:</b>")
        file_label.set_halign(Gtk.Align.START)
        
        file_value = Gtk.Label(label=self.filename)
        file_value.set_halign(Gtk.Align.START)
        file_value.set_selectable(True)  # Allow text selection
        file_value.set_wrap(True)
        
        # Virus name
        virus_label = Gtk.Label()
        virus_label.set_markup("<b>Virus:</b>")
        virus_label.set_halign(Gtk.Align.START)
        
        virus_value = Gtk.Label(label=self.virusname)
        virus_value.set_halign(Gtk.Align.START)
        virus_value.set_selectable(True)  # Allow text selection
        
        # Attach to grid
        info_grid.attach(file_label, 0, 0, 1, 1)
        info_grid.attach(file_value, 1, 0, 1, 1)
        info_grid.attach(virus_label, 0, 1, 1, 1)
        info_grid.attach(virus_value, 1, 1, 1, 1)
        
        info_frame.set_child(info_grid)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        clean_btn = Gtk.Button.new_with_label("Clean (Delete)")
        clean_btn.connect('clicked', self.on_clean_clicked)
        clean_btn.add_css_class("destructive-action")
        
        quarantine_btn = Gtk.Button.new_with_label("Quarantine")
        quarantine_btn.connect('clicked', self.on_quarantine_clicked)
        
        close_btn = Gtk.Button.new_with_label("Close")
        close_btn.connect('clicked', self.on_close_clicked)
        
        button_box.append(clean_btn)
        button_box.append(quarantine_btn)
        button_box.append(close_btn)
        
        # Assemble UI
        vbox.append(title_box)
        vbox.append(info_frame)
        vbox.append(button_box)
        
        self.set_child(vbox)
        
    def log_action(self, action):
        """Log the action to anomalies.log"""
        log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - " \
                   f"File: {self.filename}, Virus: {self.virusname}, Action: {action}\n"
        
        try:
            with open("/var/log/clamav/anomalies.log", "a") as log_file:
                log_file.write(log_entry)
        except PermissionError:
            # Fallback to user directory if no permission
            home_dir = os.path.expanduser("~")
            fallback_log = os.path.join(home_dir, "clamav_anomalies.log")
            with open(fallback_log, "a") as log_file:
                log_file.write(f"PERMISSION DENIED for system log. {log_entry}")
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def on_clean_clicked(self, button):
        """Delete the infected file"""
        try:
            if os.path.exists(self.filename):
                os.remove(self.filename)
                self.log_action("DELETED")
                self.show_message("File deleted successfully", Gtk.MessageType.INFO)
            else:
                self.show_message("File not found", Gtk.MessageType.WARNING)
        except PermissionError:
            self.show_message("Permission denied: Cannot delete file", Gtk.MessageType.ERROR)
        except Exception as e:
            self.show_message(f"Error deleting file: {str(e)}", Gtk.MessageType.ERROR)
        finally:
            self.destroy()
    
    def on_quarantine_clicked(self, button):
        """Move file to quarantine directory"""
        quarantine_dir = "/var/lib/clamav/quarantine"
        
        try:
            # Create quarantine directory if it doesn't exist
            os.makedirs(quarantine_dir, exist_ok=True)
            
            if os.path.exists(self.filename):
                # Generate quarantine filename
                base_name = os.path.basename(self.filename)
                quarantine_path = os.path.join(quarantine_dir, base_name)
                
                # Add timestamp if file already exists in quarantine
                counter = 1
                while os.path.exists(quarantine_path):
                    name, ext = os.path.splitext(base_name)
                    quarantine_path = os.path.join(
                        quarantine_dir, 
                        f"{name}_{counter}{ext}"
                    )
                    counter += 1
                
                shutil.move(self.filename, quarantine_path)
                self.log_action(f"QUARANTINED to {quarantine_path}")
                self.show_message("File moved to quarantine", Gtk.MessageType.INFO)
            else:
                self.show_message("File not found", Gtk.MessageType.WARNING)
                
        except PermissionError:
            self.show_message("Permission denied: Cannot access quarantine directory", 
                            Gtk.MessageType.ERROR)
        except Exception as e:
            self.show_message(f"Error quarantining file: {str(e)}", Gtk.MessageType.ERROR)
        finally:
            self.destroy()
    
    def on_close_clicked(self, button):
        """Close without action"""
        self.log_action("IGNORED")
        self.destroy()
    
    def show_message(self, message, message_type):
        """Show a temporary message dialog"""
        # In GTK4, use Gtk.AlertDialog instead of MessageDialog
        dialog = Gtk.AlertDialog()
        dialog.set_message(message)
        dialog.set_modal(True)
        dialog.show(self)

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description='Virus Detection Popup')
    parser.add_argument('filename', help='Path to the infected file')
    parser.add_argument('virusname', help='Name of the detected virus')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.filename or not args.virusname:
        print("Error: Both filename and virusname are required")
        sys.exit(1)
    
    # Create and run the GTK application
    app = Gtk.Application(application_id="com.example.viruspopup")
    
    def on_activate(app):
        popup = VirusPopup(args.filename, args.virusname)
        popup.present()
    
    app.connect('activate', on_activate)
    
    # Run the application
    app.run(None)

if __name__ == "__main__":
    main()
