import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import re

class BirdCodeManager:
    def __init__(self, master=None, callback=None):
        # Create a new top-level window
        self.window = tk.Toplevel(master) if master else tk.Tk()
        self.window.title("Bird Code Manager")
        self.window.geometry("800x500")
        self.window.minsize(600, 400)
        
        # Store callback for when window is closed (to refresh main program's data)
        self.callback = callback
        
        # Load the code data
        self.original_data = self.load_codes()
        self.code_data = self.original_data.copy()
        
        # Track if changes have been made
        self.has_unsaved_changes = False

        #used for tracking the use of Discard Changes button
        self.suppress_validation = False
        
        # Track currently selected item
        self.selected_code = None
        
        # Create the main layout
        self.create_layout()
        
        # Populate the list
        self.populate_code_list()
        
        # Setup protocol for window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # If not a Toplevel window, run the mainloop
        if not master:
            self.window.mainloop()
            
    def load_codes(self):
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
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            return {}
            
    def save_codes(self):
        try:
            with open("bird codes.json", "w") as f:
                json.dump(self.code_data, f, indent=4, sort_keys=True)
            self.original_data = self.code_data.copy()
            self.has_unsaved_changes = False
            self.update_status(f"Saved {len(self.code_data)} codes successfully.")
            self.window.title("Bird Code Manager")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
            return False
            
    def create_layout(self):
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a PanedWindow for resizable split
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left frame (list view)
        list_frame = ttk.Frame(self.paned_window)
        
        # Search frame at top of list view
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search label
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_var.trace("w", self.on_search_change)
        
        # Clear search button
        ttk.Button(search_frame, text="✕", width=3, 
                command=lambda: self.search_var.set("")).pack(side=tk.RIGHT)
        
        # Add alphabetical quick filters
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create A-Z buttons in rows
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(letters):
            column = i % 13
            row = i // 13
            btn = ttk.Button(filter_frame, text=letter, width=2,
                          command=lambda l=letter: self.filter_by_letter(l))
            btn.grid(row=row, column=column, padx=1, pady=1)
        
        # Show All button
        ttk.Button(filter_frame, text="All", width=4,
                  command=self.show_all_codes).grid(row=1, column=12, padx=1, pady=1)
                
        # Create the treeview for the list
        columns = ("code", "description")
        self.code_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.code_tree.heading("code", text="Code", command=lambda: self.sort_treeview("code", False))
        self.code_tree.heading("description", text="Description", command=lambda: self.sort_treeview("description", False))
        
        # Set column widths
        self.code_tree.column("code", width=80, minwidth=60)
        self.code_tree.column("description", width=200, minwidth=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.code_tree.yview)
        self.code_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.code_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add selection event to the treeview
        self.code_tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        
        # Right frame (edit panel)
        edit_frame = ttk.Frame(self.paned_window)
        
        # Create a LabelFrame for editing
        edit_label_frame = ttk.LabelFrame(edit_frame, text="Edit Bird Code")
        edit_label_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Code entry
        code_frame = ttk.Frame(edit_label_frame)
        code_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(code_frame, text="Code:").pack(side=tk.LEFT)
        self.code_var = tk.StringVar()
        self.code_entry = ttk.Entry(code_frame, textvariable=self.code_var, width=10)
        self.code_entry.pack(side=tk.LEFT, padx=5)
        
        # Code validation label
        self.code_validation = ttk.Label(code_frame, text="", foreground="red")
        self.code_validation.pack(side=tk.LEFT, padx=5)
        
        # Description entry
        desc_frame = ttk.Frame(edit_label_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(desc_frame, text="Description:").pack(anchor=tk.W)
        
        # Use Text widget instead of Entry for multi-line descriptions
        self.desc_text = tk.Text(desc_frame, height=10, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar to description
        desc_scroll = ttk.Scrollbar(self.desc_text, orient=tk.VERTICAL, command=self.desc_text.yview)
        self.desc_text.configure(yscrollcommand=desc_scroll.set)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame for edit actions
        edit_buttons = ttk.Frame(edit_label_frame)
        edit_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        # Save current edit button
        self.save_edit_btn = ttk.Button(edit_buttons, text="Apply Changes", 
                               command=self.save_current_edit, state=tk.DISABLED)
        self.save_edit_btn.pack(side=tk.LEFT, padx=5)
        
        # Discard changes button
        self.cancel_edit_btn = ttk.Button(edit_buttons, text="Discard Changes", 
                                command=self.cancel_edit, state=tk.DISABLED)
        self.cancel_edit_btn.pack(side=tk.LEFT, padx=5)
        
        # Add the frames to the paned window
        self.paned_window.add(list_frame, weight=1)
        self.paned_window.add(edit_frame, weight=1)
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Add new code button (left)
        ttk.Button(button_frame, text="Add New Code", 
                command=self.add_new_code).pack(side=tk.LEFT, padx=5)

        # Delete code button (left)
        self.delete_btn = ttk.Button(button_frame, text="Delete Selected", 
                                    command=self.delete_selected_code, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        # Close button (far right)
        ttk.Button(button_frame, text="Close", command=self.on_close).pack(side=tk.RIGHT, padx=5)

        # Save all changes button (just left of Close)
        self.save_all_btn = ttk.Button(button_frame, text="Save All Changes", 
                                    command=self.save_codes, state=tk.DISABLED)
        self.save_all_btn.pack(side=tk.RIGHT, padx=5)


        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        
        # Set up validation for code entry
        self.code_var.trace("w", self.validate_code)
        
        # Initial state setup
        self.set_edit_mode(False)
        # Initialize original_edit to avoid issues on first selection
        self.original_edit = {"code": "", "description": ""}

        self.desc_text.bind("<<Modified>>", self.on_description_modified)

    def on_description_modified(self, event):
        self.desc_text.edit_modified(False)

        if self.suppress_validation:
            return

        self.validate_code()
    
    def populate_code_list(self, filter_text=None):
        # Clear existing items
        self.code_tree.delete(*self.code_tree.get_children())
        
        # Add all codes from data to tree
        sorted_codes = sorted(self.code_data.items())
        
        for code, description in sorted_codes:
            # Apply filter if one is provided
            if filter_text:
                if filter_text.startswith("^"):  # Letter filter
                    if not code.startswith(filter_text[1:]):
                        continue
                else:  # Text search
                    filter_lower = filter_text.lower()
                    if (filter_lower not in code.lower() and 
                        filter_lower not in description.lower()):
                        continue
            
            # Description to display may be truncated
            display_desc = description
            if len(display_desc) > 50:
                display_desc = display_desc[:47] + "..."
                
            # Insert item into tree
            self.code_tree.insert("", tk.END, values=(code, display_desc))
        
        # Update status
        count = len(self.code_tree.get_children())
        total = len(self.code_data)
        if filter_text:
            self.update_status(f"Showing {count} of {total} codes")
        else:
            self.update_status(f"Total: {total} codes")
    
    def on_search_change(self, *args):
        search_text = self.search_var.get().strip()
        self.populate_code_list(search_text)
        
    def filter_by_letter(self, letter):
        self.search_var.set(f"^{letter}")
        
    def show_all_codes(self):
        self.search_var.set("")
        
    def sort_treeview(self, column, reverse):
        # Get all items with their values
        item_list = [(self.code_tree.set(item, column), item) for item in 
                     self.code_tree.get_children('')]
        
        # Sort the list
        item_list.sort(reverse=reverse)
        
        # Move items in the sorted positions
        for index, (val, item) in enumerate(item_list):
            self.code_tree.move(item, '', index)
        
        # Reverse sort next time
        self.code_tree.heading(column, command=lambda: self.sort_treeview(column, not reverse))
        
    def on_item_selected(self, event):
        self.window.after_idle(self.handle_selection)

    def handle_selection(self):
        selection = self.code_tree.selection()
        if selection:
            item = selection[0]
            values = self.code_tree.item(item, "values")
            code = values[0]

            if code != self.selected_code:
                if self.has_unsaved_edit():
                    if messagebox.askyesno("Unsaved Changes", 
                                        "Save changes to the current code?"):
                        self.save_current_edit()

                # Fill in the edit fields
                self.code_var.set(code)
                self.desc_text.config(state=tk.NORMAL)
                self.desc_text.delete("1.0", tk.END)
                self.desc_text.insert("1.0", self.code_data[code])

                # Update buttons
                self.set_edit_mode(True)
                self.delete_btn.config(state=tk.NORMAL)

                # Reset edit state AFTER populating fields
                description = self.desc_text.get("1.0", tk.END).rstrip("\n")
                self.original_edit = {
                    "code": code,
                    "description": description
                }

                # Now set the selected code
                self.selected_code = code

                self.validate_code()

        
    def validate_code(self, *args):
        code = self.code_var.get().strip().upper()
        
        # Check if valid
        if not code:
            self.code_validation.config(text="Required", foreground="red")
            self.save_edit_btn.config(state=tk.DISABLED)
            return False
            
        if len(code) != 4:
            self.code_validation.config(text="Must be 4 letters", foreground="red")
            self.save_edit_btn.config(state=tk.DISABLED)
            return False
            
        if not code.isalpha():
            self.code_validation.config(text="Letters only", foreground="red")
            self.save_edit_btn.config(state=tk.DISABLED)
            return False
            
        # Check if it would create a duplicate (unless it's the original code)
        if code in self.code_data and code != self.selected_code:
            self.code_validation.config(text="Already exists", foreground="red")
            self.save_edit_btn.config(state=tk.DISABLED)
            return False
            
        # All checks passed
        self.code_validation.config(text="✓", foreground="green")
        
        # Enable save button if we have changes
        if self.has_unsaved_edit():
            self.save_edit_btn.config(state=tk.NORMAL)
            self.cancel_edit_btn.config(state=tk.NORMAL)
        else:
            self.save_edit_btn.config(state=tk.DISABLED)
            self.cancel_edit_btn.config(state=tk.DISABLED)
        
        # All checks passed
        self.code_validation.config(text="✓", foreground="green")

        # Enable or disable buttons based on whether changes exist
        if self.has_unsaved_edit():
            self.save_edit_btn.config(state=tk.NORMAL)
            self.cancel_edit_btn.config(state=tk.NORMAL)
        else:
            self.save_edit_btn.config(state=tk.DISABLED)
            self.cancel_edit_btn.config(state=tk.DISABLED)


        return True
        
    def has_unsaved_edit(self):
        if not hasattr(self, 'original_edit'):
            return False
            
        current_code = self.code_var.get().strip().upper()
        # Strip any trailing newlines for consistent comparison
        current_desc = self.desc_text.get("1.0", tk.END).rstrip("\n")
        
        return (current_code != self.original_edit["code"] or 
                current_desc != self.original_edit["description"])
        
    def set_edit_mode(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        
        self.code_entry.config(state=state)
        self.desc_text.config(state=state)
        self.save_edit_btn.config(state=tk.DISABLED)  # Always starts disabled
        self.cancel_edit_btn.config(state=tk.DISABLED)  # Always starts disabled
        
    def save_current_edit(self):
        if not self.validate_code():
            return
            
        new_code = self.code_var.get().strip().upper()
        new_desc = self.desc_text.get("1.0", tk.END).strip()
        
        try:
            # If code changed, we need to delete old and add new
            if new_code != self.selected_code:
                # Remove old code
                if self.selected_code in self.code_data:
                    del self.code_data[self.selected_code]
                    
            # Add/update with new values
            self.code_data[new_code] = new_desc
            
            # Update the selected code
            self.selected_code = new_code
            
            # Reset edit state
            self.original_edit = {
                "code": new_code,
                "description": new_desc
            }
            
            # Update the tree view
            self.populate_code_list(self.search_var.get().strip())
            
            # Select the new item
            for item in self.code_tree.get_children():
                if self.code_tree.item(item, "values")[0] == new_code:
                    self.code_tree.selection_set(item)
                    self.code_tree.see(item)
                    break
                    
            # Update UI state
            self.save_edit_btn.config(state=tk.DISABLED)
            self.cancel_edit_btn.config(state=tk.DISABLED)
            self.mark_changes()
            
            self.update_status(f"Updated code: {new_code}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save edit: {str(e)}")
            
    def cancel_edit(self):
        if hasattr(self, 'original_edit'):
            if self.selected_code is None:
                # New code — clear and disable form
                self.suppress_validation = True  # ⬅️ Temporarily suppress validation

                self.code_var.set("")
                self.desc_text.delete("1.0", tk.END)
                self.set_edit_mode(False)
                self.save_edit_btn.config(state=tk.DISABLED)
                self.cancel_edit_btn.config(state=tk.DISABLED)
                self.code_validation.config(text="")  # Clear validation error
                self.update_status("New code cleared")

                # Re-enable validation after idle to avoid <<Modified>> event interference
                self.window.after_idle(lambda: setattr(self, 'suppress_validation', False))

                return  # Prevent validate_code() from running below

            else:
                # Editing existing code — restore original
                self.code_var.set(self.original_edit["code"])
                self.desc_text.delete("1.0", tk.END)
                self.desc_text.insert("1.0", self.original_edit["description"])
                self.save_edit_btn.config(state=tk.DISABLED)
                self.cancel_edit_btn.config(state=tk.DISABLED)
                self.update_status("Edit cancelled")

        self.validate_code()  # Only runs for existing codes


            
    def add_new_code(self):
        # Check if we need to save current changes first
        if self.has_unsaved_edit():
            if messagebox.askyesno("Unsaved Changes", 
                                "Save changes to the current code?"):
                self.save_current_edit()
        
        # Get a unique new code suggestion
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        # Start with a valid 4-letter alphabetic code (e.g., NEWW, NEWX...)
        import string
        base = "NEW"
        suffix_chars = list(string.ascii_uppercase)
        counter = 0

        while True:
            if counter < len(suffix_chars):
                candidate = base + suffix_chars[counter]
            else:
                candidate = "N" + suffix_chars[counter // len(suffix_chars) % 26] + \
                            suffix_chars[counter % 26] + "X"
            if candidate not in self.code_data:
                break
            counter += 1

        new_code = candidate

        # Set up for editing the new code
        self.selected_code = None  # Not saved yet
        self.code_var.set(new_code)
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", "")
        
        # Set edit mode
        self.set_edit_mode(True)
        self.delete_btn.config(state=tk.DISABLED)  # Can't delete unsaved
        
        # Reset edit state with empty values
        self.original_edit = {
            "code": "",
            "description": ""
        }
        
        # Highlight code field for editing
        self.code_entry.select_range(0, tk.END)
        self.code_entry.focus()
        
        # Validate to update state and buttons
        self.validate_code()

        # Always allow editing after new code creation
        self.save_edit_btn.config(state=tk.NORMAL)
        self.cancel_edit_btn.config(state=tk.NORMAL)

        
        self.update_status("Creating new code")
        
    def delete_selected_code(self):
        if not self.selected_code:
            return
            
        if messagebox.askyesno("Confirm Delete", 
                             f"Are you sure you want to delete '{self.selected_code}'?"):
            try:
                # Delete from data
                if self.selected_code in self.code_data:
                    del self.code_data[self.selected_code]
                
                # Update the tree view
                self.populate_code_list(self.search_var.get().strip())
                
                # Clear selection
                self.selected_code = None
                self.code_var.set("")
                self.desc_text.delete("1.0", tk.END)
                
                # Update UI state
                self.set_edit_mode(False)
                self.delete_btn.config(state=tk.DISABLED)
                self.mark_changes()
                
                self.update_status("Code deleted")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def mark_changes(self):
        # Check if we have unsaved changes
        if self.original_data != self.code_data:
            if not self.has_unsaved_changes:
                self.has_unsaved_changes = True
                self.window.title("Bird Code Manager *")
                self.save_all_btn.config(state=tk.NORMAL)
        else:
            self.has_unsaved_changes = False
            self.window.title("Bird Code Manager")
            self.save_all_btn.config(state=tk.DISABLED)
            
    def update_status(self, message):
        self.status_var.set(message)
        
    def on_close(self):
        # Check for unsaved changes
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", 
                                               "Save changes before closing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_codes():
                    # If save failed, don't close
                    return
        
        # Call callback if provided
        if self.callback:
            self.callback()
            
        # Close window
        self.window.destroy()

# Function to replace open_codes_file
def open_codes_manager(master=None):
    """Opens the bird code manager window instead of the raw file"""
    # Create the manager window, pass the master window
    # and a callback to reload codes after editing
    BirdCodeManager(master, callback=lambda: reload_codes())
    
    return True

# Function to reload codes after editing
def reload_codes():
    global code_map
    code_map = load_codes()
    return True

# For testing purposes
if __name__ == "__main__":
    BirdCodeManager()