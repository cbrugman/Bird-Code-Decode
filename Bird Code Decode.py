import json
import tkinter as tk
import pyperclip
import threading
import platform
import pyautogui
import os
import sys
import time
from pynput import keyboard
import pystray
from PIL import Image, ImageDraw, ImageFont
from tkinter import messagebox, simpledialog

# ------- CONFIGURATION -------
# Auto-close time in milliseconds
POPUP_DURATION = 3000  

# Popup appearance
POPUP_BG = "black"
POPUP_FG = "white"
POPUP_FONT = ("Arial", 14)
# ---------------------------

# Global variables
code_map = None
tray_icon = None
setup_aborted = False

# Load the code data from JSON file
def load_codes():
    try:
        with open("bird codes.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Sample data as fallback
        sample_data = {"TEST": "This is a test code", "ABCD": "Sample code description"}
        # Save sample data
        with open("bird codes.json", "w") as f:
            json.dump(sample_data, f, indent=4)
        return sample_data
    except Exception as e:
        return {"ERROR": "Failed to load data"}

# Function to open the codes file
def open_codes_file():
    """Opens the bird code manager window instead of the raw file"""
    try:
        # Import and use the BirdCodeManager class
        from bird_code_manager import BirdCodeManager
        
        # Create the manager window with current root window as master
        # and reload_codes as callback to refresh data after editing
        BirdCodeManager(None, callback=lambda: reload_codes())
        
        return True
    except Exception as e:
        show_popup(f"Error opening code manager:\n{str(e)}")
        return False

# Reload codes after editing
def reload_codes():
    global code_map
    code_map = load_codes()
    return True

# Create a simple icon image
def create_icon_image():
    # Create a blank image for the icon, 64x64 pixels
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    # Draw a simple icon - white square with rounded corners
    draw.rectangle((10, 10, 54, 54), fill=(255, 255, 255), outline=(255, 255, 255), width=2)
    # Add a small "B" in the center to represent "Bird Code"
    draw.text((32, 32), "B", fill=(0, 0, 0))
    return image

# Show the welcome screen
def show_welcome_screen():
    welcome = tk.Tk()
    welcome.title("Welcome to Bird Code Decode")
    welcome.geometry("600x700")  # Increased size to fit all content
    welcome.configure(bg="#f0f0f0")
    
    # Main frame
    main_frame = tk.Frame(welcome, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # App title
    title_label = tk.Label(
        main_frame, 
        text="Bird Code Decode", 
        font=("Arial", 18, "bold"),
        bg="#f0f0f0"
    )
    title_label.pack(pady=(0, 15))
    
    # Welcome message
    welcome_text = """
Welcome to Bird Code Decode, a tool that helps you quickly look up bird species
from their 4-letter codes.
    """
    welcome_label = tk.Label(
        main_frame,
        text=welcome_text,
        font=("Arial", 12),
        justify=tk.LEFT,
        bg="#f0f0f0"
    )
    welcome_label.pack(pady=(0, 10), anchor=tk.W)

    # Instructions frame
    instructions_frame = tk.LabelFrame(
        main_frame,
        text="How to Use",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    instructions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Instructions text
    instructions_text = """
1. Copy a 4-letter bird code to your clipboard
   • Select the text and press Ctrl+C
   • Or right-click and select 'Copy'

2. Press the decode hotkey (Ctrl+Shift+L)

3. A popup will appear showing the full bird name
    """
    instructions_label = tk.Label(
        instructions_frame,
        text=instructions_text,
        font=("Arial", 12),
        justify=tk.LEFT,
        bg="#f0f0f0"
    )
    instructions_label.pack(anchor=tk.W)
    
    # Tips frame
    tips_frame = tk.LabelFrame(
        main_frame,
        text="Tips",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    tips_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Tips text
    tips_text = """
• Bird Code Decode runs in your system tray
• Right-click the system tray icon for options
• You can edit your bird code database from the tray menu
    """
    tips_label = tk.Label(
        tips_frame,
        text=tips_text,
        font=("Arial", 12),
        justify=tk.LEFT,
        bg="#f0f0f0"
    )
    tips_label.pack(anchor=tk.W)
    
    # Don't show again checkbox
    show_again_var = tk.BooleanVar(value=True)
    show_again_check = tk.Checkbutton(
        main_frame,
        text="Show this screen on startup",
        variable=show_again_var,
        onvalue=True,
        offvalue=False,
        bg="#f0f0f0"
    )
    show_again_check.pack(anchor=tk.W, pady=(10, 0))
    
    # Close button
    close_button = tk.Button(
        main_frame,
        text="Get Started",
        command=lambda: close_welcome(show_again_var.get()),
        font=("Arial", 12),
        padx=20
    )
    close_button.pack(pady=15)
    
    # Function to handle closing the welcome screen
    def close_welcome(show_again):
        # Save the user's preference
        try:
            config_file = "app_config.json"
            config = {}
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)
            
            config["show_welcome"] = show_again
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
        
        # Destroy window and ensure resources are released
        welcome.destroy()
        welcome.quit()
    
    # Center the window on screen
    welcome.update_idletasks()
    width = welcome.winfo_width()
    height = welcome.winfo_height()
    x = (welcome.winfo_screenwidth() // 2) - (width // 2)
    y = (welcome.winfo_screenheight() // 2) - (height // 2)
    welcome.geometry(f'+{x}+{y}')
    
    welcome.mainloop()

# Check if we should show welcome screen
def should_show_welcome():
    try:
        config_file = "app_config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                return config.get("show_welcome", True)
        # Create default config file if it doesn't exist
        with open(config_file, "w") as f:
            json.dump({"show_welcome": True}, f, indent=4)
        return True  # Default to showing welcome
    except Exception:
        return True  # Show welcome on any error

# Set up the system tray icon with menu
def setup_tray_icon():
    # Create a global variable for the icon so it doesn't get garbage collected
    global tray_icon
    
    # Function to exit the application
    def exit_action(icon):
        icon.stop()
        os._exit(0)
    
    # Function to show the help popup
    def show_help(icon):
        show_popup("Bird Code Decode\n\nHotkey: Ctrl+Shift+L\n\nCopy a 4-letter code to clipboard\nthen press the hotkey.")
    
    # Function to edit codes
    def edit_codes(icon):
        open_codes_file()
    
    # Function to show welcome screen
    def open_welcome(icon):
        show_welcome_screen()
    
    try:
        # Create the menu
        menu = pystray.Menu(
            pystray.MenuItem("Show Welcome", open_welcome),
            pystray.MenuItem("Edit Codes", edit_codes),
            pystray.MenuItem("Help", show_help),
            pystray.MenuItem("Quit", exit_action)
        )
        
        # Create the icon
        icon_image = create_icon_image()
        
        tray_icon = pystray.Icon(
            "BirdCode",
            icon=icon_image,
            menu=menu,
            title="Bird Code Decode"
        )
                
        # Start the icon in a separate thread - NON-DAEMON so it keeps program alive
        icon_thread = threading.Thread(target=tray_icon.run)
        icon_thread.daemon = False
        icon_thread.start()
                
        return tray_icon
        
    except Exception as e:
        return None

# Show popup window at mouse position
def show_popup(message):
    try:
        # Get current mouse position
        mouse_x, mouse_y = pyautogui.position()
        
        # Function to create and display the popup
        def create_popup():
            # Create root window
            popup = tk.Tk()
            popup.withdraw()  # Hide initially
            popup.overrideredirect(True)  # Remove title bar and borders
            popup.attributes("-topmost", True)  # Keep on top
            
            # Create a frame with border
            frame = tk.Frame(popup, bg=POPUP_BG, padx=15, pady=10,
                           highlightbackground="white", highlightthickness=1)
            frame.pack()
            
            # Add the text label
            label = tk.Label(frame, text=message, bg=POPUP_BG, fg=POPUP_FG,
                           font=POPUP_FONT, justify=tk.LEFT)
            label.pack()
            
            # Position window near mouse cursor
            popup.update_idletasks()
            width = popup.winfo_width()
            height = popup.winfo_height()
            
            popup.geometry(f"+{mouse_x + 20}+{mouse_y + 20}")
            popup.deiconify()  # Make visible
            popup.update()  # Force update to show immediately
            
            # Auto-close after set duration
            popup.after(POPUP_DURATION, popup.destroy)
            popup.mainloop()
        
        # Run in a new thread to avoid blocking
        thread = threading.Thread(target=create_popup)
        thread.daemon = True
        thread.start()
        
        return True
        
    except Exception as e:
        #print(f"Error showing popup: {e}")
        return False

def get_clipboard_text():
    try:
        current_os = platform.system()
        if current_os == "Linux":
            # pyperclip should work if xclip or xsel is installed
            return pyperclip.paste()
        elif current_os == "Windows" or current_os == "Darwin":
            return pyperclip.paste()
        else:
            return None
    except pyperclip.PyperclipException:
        return None

# Action to perform when hotkey is triggered
def on_hotkey_action():
    try:
        # Get text from clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text is None:
            show_popup("Clipboard access failed.\nOn Linux, install 'xclip' or 'xsel'.")
            return

        
        # Check if clipboard is empty
        if not clipboard_text:
            show_popup("Clipboard is empty.\nCopy a 4-letter code first.")
            return
            
        # Trim and convert to uppercase
        clipboard_text = clipboard_text.strip().upper()
        
        # Check if it's a valid 4-letter code
        if len(clipboard_text) == 4 and clipboard_text.isalpha():
            # Look up the code
            result = code_map.get(clipboard_text, "Code not found")
            # Show the result
            show_popup(f"{clipboard_text}: {result}")
        else:
            # Invalid code format - show more detailed error
            if len(clipboard_text) > 20:
                # If clipboard content is very long, truncate it
                clipboard_preview = clipboard_text[:17] + "..."
                show_popup(f"Invalid content: '{clipboard_preview}'\nNeed a 4-letter code.")
            else:
                show_popup(f"Invalid code: '{clipboard_text}'\nNeed a 4-letter code.")
    except pyperclip.PyperclipException:
        show_popup("Could not access clipboard.\nPlease try again.")
    except Exception as e:
        # A more detailed error message for debugging
        error_msg = str(e)
        if len(error_msg) > 50:  # Truncate very long error messages
            error_msg = error_msg[:47] + "..."
        show_popup(f"Error processing clipboard:\n{error_msg}")

# Run a test popup
def test_popup():
    #print("Showing test popup...")
    # Get the currently active window
    try:
        # Try to show popup
        show_popup("Bird Code Decode\n\nHotkey: Ctrl+Shift+L\n\nCopy a 4-letter bird code to clipboard\nthen press the hotkey.")
        return True
    except Exception as e:
        #print(f"Error showing popup: {e}")
        return False

# Main application function
def main():
    
    global setup_aborted
    
    # Load codes first
    global code_map
    code_map = load_codes()
    
    # Check for first-time setup by looking for config files
    key_file = "hotkey_config.json"
    config_file = "app_config.json"
    first_time_ever = not (os.path.exists(key_file) or os.path.exists(config_file))
    
    # For the very first run, show welcome screen BEFORE hotkey setup
    if first_time_ever:
        # Show welcome screen first
        show_welcome_screen()
        
        # Then set up keyboard listener
        result = setup_keyboard_listener()
        if result is None or result[0] is None:
            print("Setup was aborted. Exiting application.")
            return
            
        listener, first_time_setup = result
    else:
        # Normal flow for subsequent runs
        result = setup_keyboard_listener()
        if result is None or result[0] is None:
            print("Setup was aborted. Exiting application.")
            return
            
        listener, first_time_setup = result
    
    # Start the listener
    listener.start()
    
    # Set up the system tray icon
    setup_tray_icon()
    
    # Only show welcome screen on subsequent runs if user has opted to see it
    if not first_time_ever and (first_time_setup or should_show_welcome()):
        show_welcome_screen()
    elif not first_time_ever:
        # If not showing welcome, show test popup instead
        test_popup()
    
    # This is the key part: keep the main thread alive
    try:
        print("Entering main loop")
        # Keep program running indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        print("Shutting down...")
        # Perform cleanup
        if tray_icon is not None:
            tray_icon.stop()

# Run setup keyboard listener function (keeping it unchanged)
def setup_keyboard_listener():
    global setup_aborted  # Access the global flag
    
    # First check if we have a saved key detection
    key_file = "hotkey_config.json"
    hotkey_char = None
    
    # Flag to indicate if we're running configuration
    first_time_setup = False
    
    try:
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                config = json.load(f)
                # The actual key code might be stored as an escape sequence
                if "hotkey_code" in config:
                    hotkey_char = config["hotkey_code"]
                    # Convert string representation back to actual character
                    if hotkey_char.startswith("\\x"):
                        hotkey_char = bytes(hotkey_char, "utf-8").decode("unicode_escape")
    except Exception:
        pass
    
    # If we don't have a saved key, run the setup wizard
    if not hotkey_char:
        # Set the flag to indicate we're running first-time setup
        first_time_setup = True
        
        # Run setup wizard to detect the key
        detected_key = run_setup_wizard()
        
        # Check if setup was aborted
        if setup_aborted:
            return None, True  # Return None for listener and True for setup_aborted
        
        if detected_key and hasattr(detected_key, "char"):
            hotkey_char = detected_key.char
            
            # Save the detected key for future use
            try:
                # Store as a string representation of the character
                config = {"hotkey_code": repr(hotkey_char)[1:-1]}
                with open(key_file, "w") as f:
                    json.dump(config, f)
            except Exception:
                pass
    
    # If we still don't have a hotkey character, use a default as fallback
    if not hotkey_char:
        # Common variants for the 'L' key
        hotkey_char = '\x0c'  # Most commonly detected for 'L'
    
    # Track currently pressed keys
    pressed_keys = set()
    
    # Define hotkey combinations
    COMBINATIONS = [
        {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char(hotkey_char)},
        {keyboard.Key.ctrl_r, keyboard.Key.shift, keyboard.KeyCode.from_char(hotkey_char)},
        {keyboard.Key.ctrl_l, keyboard.Key.shift_l, keyboard.KeyCode.from_char(hotkey_char)},
        {keyboard.Key.ctrl_l, keyboard.Key.shift_r, keyboard.KeyCode.from_char(hotkey_char)},
        {keyboard.Key.ctrl_r, keyboard.Key.shift_l, keyboard.KeyCode.from_char(hotkey_char)},
        {keyboard.Key.ctrl_r, keyboard.Key.shift_r, keyboard.KeyCode.from_char(hotkey_char)},
    ]
    
    # Timestamp to prevent multiple rapid triggers
    last_triggered = 0
    
    def on_press(key):
        nonlocal last_triggered
        
        try:
            # Handle various forms of shift and ctrl keys
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                pressed_keys.add(keyboard.Key.shift)
                pressed_keys.add(key)
            elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                pressed_keys.add(keyboard.Key.ctrl)
                pressed_keys.add(key)
            else:
                pressed_keys.add(key)
            
            # Check for direct match with hotkey character
            if isinstance(key, keyboard.KeyCode) and hasattr(key, "char") and key.char == hotkey_char:
                # Also check for modifier keys
                if ((keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys) and 
                    (keyboard.Key.shift in pressed_keys or keyboard.Key.shift_l in pressed_keys or keyboard.Key.shift_r in pressed_keys)):
                    
                    current_time = time.time()
                    if current_time - last_triggered > 0.5:
                        last_triggered = current_time
                        on_hotkey_action()
                        return
            
            # Also check all combinations
            current_time = time.time()
            if current_time - last_triggered > 0.5:
                for combo in COMBINATIONS:
                    if all(k in pressed_keys for k in combo):
                        last_triggered = current_time
                        on_hotkey_action()
                        return
                        
        except Exception:
            pass

    def on_release(key):
        try:
            # Remove keys from set when released
            if key in pressed_keys:
                pressed_keys.remove(key)
            
            # Special handling for shift and ctrl
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                pressed_keys.discard(keyboard.Key.shift)
                pressed_keys.discard(keyboard.Key.shift_l)
                pressed_keys.discard(keyboard.Key.shift_r)
            elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                pressed_keys.discard(keyboard.Key.ctrl)
                pressed_keys.discard(keyboard.Key.ctrl_l)
                pressed_keys.discard(keyboard.Key.ctrl_r)
                
        except Exception:
            pass

    # Create and return the listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    
    # Return both the listener and the first_time_setup flag
    return listener, first_time_setup

# Run the setup wizard to detect correct hotkey character
def run_setup_wizard():
    global setup_aborted  # Use global flag to track setup status
    
    # Create a global variable to store the detected key
    detected_key = None
    
    # Create GUI for key detection
    root = tk.Tk()
    root.title("Hotkey Setup")
    root.geometry("400x300")
    root.attributes("-topmost", True)  # Keep on top
    
    # Add instructions
    tk.Label(root, text="Hotkey Setup Wizard", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(root, text="Press Ctrl+Shift+L to detect your keyboard's code", font=("Arial", 12)).pack(pady=5)
    
    # Key status display
    key_display = tk.Label(root, text="Listening for key press...", font=("Courier", 12))
    key_display.pack(pady=10)
    
    # Detection status
    status = tk.Label(root, text="Detection started automatically", fg="blue")
    status.pack(pady=5)
    
    # Button frame
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)
    
    # Function to capture keypress
    def capture_key():
        pressed_keys = set()
        last_key = None
        
        def on_press(key):
            nonlocal last_key
            # Add to pressed keys
            pressed_keys.add(key)
            # Update display
            key_str = ", ".join(str(k) for k in pressed_keys)
            key_display.config(text=f"Keys: {key_str}")
            
            # Check for Ctrl+Shift combination
            ctrl_pressed = keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys
            shift_pressed = keyboard.Key.shift in pressed_keys or keyboard.Key.shift_l in pressed_keys or keyboard.Key.shift_r in pressed_keys
            
            # If we have Ctrl+Shift and a character key is pressed
            if ctrl_pressed and shift_pressed and key not in (
                keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, 
                keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r
            ):
                # This is likely our 'L' key
                last_key = key
                # Show detection
                status.config(text=f"Detected: {key}", fg="green")
                # Stop listener
                return False
        
        def on_release(key):
            # Remove from pressed keys
            if key in pressed_keys:
                pressed_keys.remove(key)
            
        # Create and start listener
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        
        # Return the last detected key (our 'L' equivalent)
        return last_key
    
    # Function to start detection
    def start_detection():
        # Ensure window has focus
        root.focus_force()
        root.lift()
        
        status.config(text="Listening for keypress...", fg="blue")
        # Start detection in a thread to avoid freezing UI
        def detection_thread():
            nonlocal detected_key
            detected_key = capture_key()
            # Update status when complete
            if detected_key:
                status.config(text=f"Detection complete! Detected: {detected_key}", fg="green")
                save_btn.config(state=tk.NORMAL)
                # Force focus back to the setup window
                root.after(100, lambda: root.focus_force())
            else:
                status.config(text="No key detected, try again", fg="red")
                # Automatically restart detection if failed
                root.after(1000, start_detection)
        
        threading.Thread(target=detection_thread, daemon=True).start()
    
    # Function to save and exit
    def save_and_exit():
        # Add a small delay before destroying to ensure configs are saved
        time.sleep(0.2)
        root.destroy()
    
    # Function to handle window close
    def on_closing():
        global setup_aborted
        if detected_key:
            save_and_exit()
        else:
            # Ask user if they want to exit without detecting a key
            if messagebox.askyesno("Confirm Exit", "Exit without setting up hotkey?"):
                setup_aborted = True  # Set flag to indicate setup was aborted
                root.destroy()
    
    # Set protocol for window close
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Add buttons - now we only need the Save button
    restart_btn = tk.Button(btn_frame, text="Restart Detection", command=start_detection)
    restart_btn.pack(side=tk.LEFT, padx=10)
    
    save_btn = tk.Button(btn_frame, text="Save & Continue", command=save_and_exit, state=tk.DISABLED)
    save_btn.pack(side=tk.LEFT, padx=10)
    
    # Ensure window is focused and start detection automatically
    root.after(100, lambda: (root.focus_force(), start_detection()))
    
    # Run the GUI
    root.mainloop()
    
    # Return the detected key
    return detected_key

if __name__ == "__main__":
    main()