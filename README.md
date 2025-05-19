🐦 **Bird Code Decode**  
Bird Code Decode is a lightweight Windows utility that monitors your clipboard for 4-letter bird banding codes and instantly displays their full bird name in a popup. It's especially handy for birders or naturalists dealing with standardized codes from organizations like the Bird Banding Lab (e.g., "AMRO" → "American Robin").  

✨ **Features**  
Uses the clipboard to retrieve 4-letter bird code  
Activated via a global hotkey (default: Ctrl+Shift+L)  
Displays a popup with the decoded bird name  
Runs silently in the background with system tray support  
Automatically starts minimized to tray  

🛠 **Installation**  
Clone or download this repository.

1. Install the required Python packages:
  pip install pyperclip keyboard pystray pillow
2. Run the script:
  python "Bird Code Decode.py"

🚀 **Usage**  
Copy any 4-letter bird banding code to your clipboard (e.g., AMRO).

Press the hotkey: Ctrl+Shift+L.

A popup will show the corresponding bird name:
  AMRO = American Robin
