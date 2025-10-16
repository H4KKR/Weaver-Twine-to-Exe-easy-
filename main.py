import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import uuid # Import the UUID library
import PyInstaller.__main__ # The core change: import PyInstaller's main module
import PyQt5
from PyQt5.QtWebEngineWidgets import QWebEngineView

print("running")

# The code for the main application, which will be written to a temporary file.
MAIN_APP_CODE = """
import sys
import os
import configparser
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon

def create_html_viewer(html_file_path, icon_file_path, window_title):
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon(icon_file_path))

    # Create the main window
    main_window = QMainWindow()
    main_window.setWindowTitle(window_title)
    main_window.setGeometry(100, 100, 1280, 720)

    # Create the web view widget
    web_view = QWebEngineView()
    
    # Load the local HTML file
    file_url = QUrl.fromLocalFile(html_file_path)
    web_view.load(file_url)
    
    # Set the web view as the central widget
    main_window.setCentralWidget(web_view)
    
    # Show the window and start the application's event loop
    main_window.show()
    sys.exit(app.exec_())

def load_config(base_path):
    config = configparser.ConfigParser()
    config_file_path = os.path.join(base_path, 'config.conf')
    
    html_file = None
    icon_path = None
    window_title = None
    
    if os.path.exists(config_file_path):
        try:
            config.read(config_file_path)
            html_file = os.path.join(base_path, config['Paths'].get('html_file'))
            icon_path = os.path.join(base_path, config['Paths'].get('icon_path'))
            window_title = config['Paths'].get('window_title')
            print(f"Config file loaded successfully from {config_file_path}")
        except (configparser.Error, KeyError) as e:
            print(f"Error reading config file: {e}. Using default paths.")
    
    # Fallback to default paths and title if config fails or doesn't exist
    if not icon_path:
        icon_path = ''
    if not window_title:
        window_title = "My Project"
    
    return html_file, icon_path, window_title

if __name__ == "__main__":
    # Determine the correct base path for bundled files
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Load paths and title from the configuration file or use defaults
    html_file, icon_path, window_title = load_config(base_path)
    
    print(f"Attempting to load HTML file from: {html_file}")
    print(f"Attempting to load icon file from: {icon_path}")
    print(f"Setting window title to: {window_title}")
    
    # Check if the HTML file exists before trying to display it
    if os.path.exists(html_file):
        create_html_viewer(html_file, icon_path, window_title)
    else:
        print(f"Error: HTML file not found at {html_file}")
        sys.exit(1)
"""

CONF = """
[Paths]
html_file = {}
icon_path = {}
window_title = {}
"""

class AppBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HTML to EXE Builder")
        self.geometry("600x480")
        self.config(bg="#f0f0f0")
        
        self.html_file_path = ""
        self.images_folder_path = ""
        self.icon_file_path = ""
        self.output_dir_path = ""
        
        self.create_widgets()

    def create_widgets(self):
        # Frame for Project Name
        name_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        name_frame.pack(fill="x", padx=20)
        tk.Label(name_frame, text="Project Name:", bg="#f0f0f0").pack(side="left")
        self.name_entry = tk.Entry(name_frame, width=50)
        self.name_entry.insert(0, "MyWebApp") # Default name
        self.name_entry.pack(side="left", padx=5)

        # Frame for HTML file selection
        html_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        html_frame.pack(fill="x", padx=20)
        tk.Label(html_frame, text="Select HTML File:", bg="#f0f0f0").pack(side="left")
        self.html_entry = tk.Entry(html_frame, width=50)
        self.html_entry.pack(side="left", padx=5)
        tk.Button(html_frame, text="Browse", command=self.select_html_file).pack(side="left")

        # Frame for Images folder selection
        images_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        images_frame.pack(fill="x", padx=20)
        tk.Label(images_frame, text="Select Images Folder:", bg="#f0f0f0").pack(side="left")
        self.images_entry = tk.Entry(images_frame, width=50)
        self.images_entry.pack(side="left", padx=5)
        tk.Button(images_frame, text="Browse", command=self.select_images_folder).pack(side="left")
        
        # Frame for Icon file selection
        icon_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        icon_frame.pack(fill="x", padx=20)
        tk.Label(icon_frame, text="Select Icon File:", bg="#f0f0f0").pack(side="left")
        self.icon_entry = tk.Entry(icon_frame, width=50)
        self.icon_entry.pack(side="left", padx=5)
        tk.Button(icon_frame, text="Browse", command=self.select_icon_file).pack(side="left")

        # Frame for Output Directory selection
        output_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        output_frame.pack(fill="x", padx=20)
        tk.Label(output_frame, text="Select Output Directory:", bg="#f0f0f0").pack(side="left")
        self.output_entry = tk.Entry(output_frame, width=50)
        self.output_entry.pack(side="left", padx=5)
        tk.Button(output_frame, text="Browse", command=self.select_output_dir).pack(side="left")
      

        # Build button
        self.build_button = tk.Button(self, text="Build EXE", command=self.start_build_thread, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
        self.build_button.pack(pady=20)

        # Output label
        self.status_label = tk.Label(self, text="Status: Ready", bg="#f0f0f0")
        self.status_label.pack(pady=10)

    def select_html_file(self):
        file_path = filedialog.askopenfilename(
            title="Select HTML File",
            filetypes=(("HTML files", "*.html"), ("All files", "*.*"))
        )
        if file_path:
            self.html_file_path = file_path
            self.html_entry.delete(0, tk.END)
            self.html_entry.insert(0, file_path)
            self.status_label.config(text=f"Status: HTML file selected: {os.path.basename(file_path)}")

    def select_images_folder(self):
        folder_path = filedialog.askdirectory(title="Select Images Folder")
        if folder_path:
            self.images_folder_path = folder_path
            self.images_entry.delete(0, tk.END)
            self.images_entry.insert(0, folder_path)
            self.status_label.config(text=f"Status: Images folder selected: {os.path.basename(folder_path)}")

    def select_icon_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=(("Icon files", "*.ico"), ("All files", "*.*"))
        )
        if file_path:
            self.icon_file_path = file_path
            self.icon_entry.delete(0, tk.END)
            self.icon_entry.insert(0, file_path)
            self.status_label.config(text=f"Status: Icon file selected: {os.path.basename(file_path)}")
    
    def select_output_dir(self):
        folder_path = filedialog.askdirectory(title="Select Output Directory")
        if folder_path:
            self.output_dir_path = folder_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder_path)
            self.status_label.config(text=f"Status: Output directory selected: {os.path.basename(folder_path)}")


    def build_exe(self):
        print("inside build_exe")
        # Validation and status updates
        project_name = self.name_entry.get().strip()
        if not project_name:
            messagebox.showerror("Error", "Please enter a project name.")
            self.status_label.config(text="Status: Failed")
            return
            
        if not self.html_file_path or not os.path.exists(self.html_file_path):
            messagebox.showerror("Error", "Please select a valid HTML file.")
            self.status_label.config(text="Status: Failed")
            return
        
        if not self.images_folder_path or not os.path.exists(self.images_folder_path):
            messagebox.showerror("Error", "Please select a valid images folder.")
            self.status_label.config(text="Status: Failed")
            return
        
        if not self.output_dir_path or not os.path.exists(self.output_dir_path):
            messagebox.showerror("Error", "Please select a valid output directory.")
            self.status_label.config(text="Status: Failed")
            return
 
 
        self.status_label.config(text="Status: Building EXE, please wait...")
        self.update_idletasks()

        # Generate a unique temporary filename
        temp_main_app_filename = f"_temp_main_app_{uuid.uuid4()}.py"
        temp_conf_filename = "config.conf"

        # Get the path to the directory containing this script
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use os.path.join to create the full, absolute path for the temporary file
        temp_main_app_path = os.path.join(project_dir, temp_main_app_filename)
        temp_conf_path = os.path.join(project_dir, temp_conf_filename)

        html_file_basename = os.path.basename(self.html_file_path)
        images_folder_basename = os.path.basename(self.images_folder_path)
        icon_file_basename = os.path.basename(self.icon_file_path)
        script_basename = os.path.basename(temp_main_app_filename)


        # Write the main app code to a temporary file
        try:
            with open(temp_main_app_path, "w") as f:
                f.write(MAIN_APP_CODE)
                print(f"created temporary script at {temp_main_app_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create temporary script: {e}")
            self.status_label.config(text="Status: Failed")
            return
        
        try:
            with open(temp_conf_path, "w") as f:
                f.write(CONF.format(html_file_basename, icon_file_basename, project_name))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create temporary script: {e}")
            self.status_label.config(text="Status: Failed")
            return
            
        # Create the pyinstaller arguments list
        # PyInstaller's programmatic API expects a list of arguments, just like the command line.
        
        pyinstaller_args = [
            '--onefile',
            '--noconsole', # Added to make the final exe run without a console window
            '--collect-all', 'PyQt5.QtWebEngineWidgets',
            f'--add-data={self.images_folder_path}{os.pathsep}{images_folder_basename}',
            f'--add-data={self.html_file_path}{os.pathsep}.',
            f'--add-data={temp_conf_path}{os.pathsep}.',
            f'--name={project_name}',
            f'--distpath={self.output_dir_path}',
            temp_main_app_path, # The script to build must be the last argument
        ]
        
        # Add icon flag if an icon file was selected
        if self.icon_file_path and os.path.exists(self.icon_file_path):
            pyinstaller_args.append(f'--icon={self.icon_file_path}')
            pyinstaller_args.append(f'--add-data={self.icon_file_path}{os.pathsep}.')

        # --- THE CORE CHANGE: USE PyInstaller's PROGRAMMATIC API ---
        try:
            PyInstaller.__main__.run(pyinstaller_args)
            messagebox.showinfo("Success", "Executable built successfully!")
            self.status_label.config(text="Status: Build successful!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during build: {e}")
            self.status_label.config(text="Status: Build failed.")
        finally:
            # Clean up the temporary file, regardless of success or failure
            if os.path.exists(temp_main_app_path):
                os.remove(temp_main_app_path)
            if os.path.exists(temp_conf_path):
                os.remove(temp_conf_path)
    
    def start_build_thread(self):
        threading.Thread(target=self.build_exe).start()


if __name__ == "__main__":
    app = AppBuilder()
    app.mainloop()