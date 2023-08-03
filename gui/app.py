import tkinter as tk
from PIL import Image, ImageTk
import webbrowser
import os
import sys
sys.path.append('./../photo_analysis')
# import photo_utils
# import light_profiles
from photo_analysis import photo_utils, light_profiles
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QWidget
from gui import widgets
from gui.image_display import ImageDisplay

class PhotoAnalyzerApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('KordeschProgram_v1.0')
        self.window.geometry("600x56")
        self.window.minsize(600, 54)

        self.imagefile = None
        self.imgpath = None
        self.file_is_open = False
        self.linewidth = 1
        self.INFO = "<Kordesch-Program, v=1.0>"
        self.all_points = []
        self.tool = None

        # Empty menubar object
        self.menubar = None
        self.filemenu = None

        self.color = "#ffff00"

        self.create_menus()
        self.create_toolbar()
        self.create_infobar()

        # Application keyboard binds
        self.window.bind("<Control-o>", self.open_image)
        self.window.bind("<Control-s>", self.save_image)
        self.window.bind("<Control-q>", self.exit_application)
        self.window.bind("<Control-f>", self.clear)

        self.window.mainloop()

    # FILE MENU COMMANDS

    def exit_application(self):
        exitapplicationwindow = widgets.ExitApplication(self.window)
        if exitapplicationwindow.check_image_open():
            exitapplicationwindow.exit_with_confirmation()
        else:
            self.window.destroy()

    def open_image(self, event=None):
        # If there is already an image opened in the canvas
        if self.file_is_open:
            msga = "There is already a file opened. Would you like to open a different file?"
            msgb = "\n(WARNING: Opening a different file will clear the current file without saving.)"
            answer = tk.messagebox.askyesnocancel(title="Open new file?", message=msga + msgb)

            if not answer:
                return

        # Get the name of the file to open
        imgpath = tk.filedialog.askopenfilename(title="Select file",
                                                filetypes=(("JPEGs", "*.jpg"), ("PNGs", "*.png"), ("All Files", "*.*")))

        # If a file is selected and no file is currently open
        if imgpath and not self.file_is_open:
            self.imagefile = ImageDisplay(self.window, imgpath)  # Open image in canvas

            self.imagefile.pack(fill=tk.BOTH, expand=tk.YES)

            # Change window geometry to dimensions of the image
            self.window.geometry(str(self.imagefile.image.width) + "x" + str(self.imagefile.image.height))

            # Enable "Save" and "Save As..." buttons in the menu
            self.filemenu.entryconfig("Save", state="normal")
            self.filemenu.entryconfig("Save As...", state="normal")

            # A file is now open
            self.file_is_open = True

        # If a file is selected and a file is currently open
        elif imgpath and self.file_is_open:
            self.imagefile._change_image(imgpath)

    def save_image(self):
        msg = "Do you want to save?\n\n(WARNING: Saving will overwrite any existing file.)"
        if tk.messagebox.askyesnocancel(title="File Save", message=msg):
            with Image.open(self.imgpath, 'w') as f:
                f.write(self.imagefile.image)

    def save_image_as(self):
        new_path = tk.filedialog.asksaveasfilename(initialdir=os.path.splitext(self.imgpath)[0],
                                                   defaultextension='.' + str(self.imagefile.image.format),
                                                   filetypes=(("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")),
                                                   initialfile=os.path.basename(self.imgpath))

        if new_path:
            with Image.open(new_path, 'w') as f:
                f.write(self.imagefile.image)

    # EDIT MENU COMMANDS

    # Clear all items from the canvas
    def clear(self):
        if self.imagefile:
            self.imagefile.background.delete("line", "aline", "rect", "point")

    # Change the width of lines drawn onto the canvas
    def line_width(self):
        self.linewidth = self.line_width_prompt()

    # Prompt to get input from user for line width
    def line_width_prompt(self):
        self.line_width_var = tk.IntVar()
        self.line_width_var.set(self.linewidth)

        top = tk.Toplevel(self.window)
        top.title("Line Width Prompt")

        tk.Label(top, text="Line Width: ").grid(row=0, column=0)
        tk.Entry(top, textvariable=self.line_width_var).grid(row=0, column=1)

        tk.Button(top, text="OK", command=self.on_line_width_ok).grid(row=1, column=0, padx=4, pady=4)
        tk.Button(top, text="Cancel", command=self.on_line_width_cancel).grid(row=1, column=1, padx=4, pady=4)

        top.protocol("WM_DELETE_WINDOW", self.on_line_width_cancel)
        top.wait_window()

        return self.line_width_var.get()

    def on_line_width_ok(self):
        self.linewidth = self.line_width_var.get()
        self.line_width_prompt_returnflag = True
        self.window.focus()

    def on_line_width_cancel(self):
        self.line_width_prompt_returnflag = False
        self.window.focus()

    # IMAGE MENU COMMANDS

    def crop_image(self):
        photo_utils.crop_image(self.imagefile, self.P1, self.P2)

    @staticmethod
    def get_angle(a, b, c):
        return photo_utils.get_angle(a, b, c)

    def set_scale(self):
        if hasattr(self, "P1") and hasattr(self, "P2"):
            photo_utils.set_scale(self.imagefile, self.window, photo_utils.get_distance(self.P1, self.P2))
        else:
            print(getattr(self))

    def rotate_image(self):
        photo_utils.rotate_image(self.window)

    # ANALYZE MENU COMMANDS

    def measure(self):
        has_required_attrs = hasattr(self, "imagefile") and hasattr(self, "P1") and hasattr(self, "P2") and hasattr(self, "table") and hasattr(self, "table_exists") and hasattr(self, "linecoords") and hasattr(self, "linewidth") and hasattr(self, "all_points")

        if has_required_attrs:
            photo_utils.measure(self.imagefile, self.P1, self.P2, self.table, self.table_exists, self.linecoords, self.linewidth, self.all_points, self.window)

    def init_ui(self):
        # ... (other UI setup code)

        # Create the PlotWidget instance and pass 'self.data' and 'self.imagefile' to the constructor
        self.plot_widget = widgets.PlotWidget(self.data, self.imagefile)

        # Add the PlotWidget to the main layout (for example, a vertical layout)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.plot_widget)

        # Create a central widget to hold the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        # Set the central widget of the main window
        self.setCentralWidget(central_widget)

    def plot_manual_profile(self):
        intensity_profile = light_profiles.IntensityProfile(self.imagefile, self.linewidth, self.P1, self.P2)
        profile = intensity_profile.get_intensity_profile()

        if profile is not None:
            # Implement code to plot the intensity profile in the plot frame
            pass
        else:
            tk.messagebox.showwarning(title="Plot Profile (Manual)", message="Point or line required.")

    def plot_automatic_profile(self):
        if not self.loaded_image:
            QMessageBox.warning(self, "Error", "Please load an image first.")
            return

        if not self.profile_available:
            QMessageBox.warning(self, "Error", "Please analyze the image first.")
            return

        if not self.intensity_profile:
            QMessageBox.warning(self, "Error", "No intensity profile data available.")
            return

        try:
            intensity_profile = light_profiles.IntensityProfile(self.img_path)
            row_profiles, col_profiles, _, _, _, _, _ = intensity_profile.automatic_profiler()

            self.clear_plots()

            # Plot the intensity profiles for rows
            for i, row_profile in enumerate(row_profiles):
                x_vals = range(len(row_profile))
                label = f"Row {i + 1}"
                self.plot_widget.plot(x_vals, row_profile, label=label) #Note: Create plot_widget method that calls PlotWidget class from widgets.py

            # Plot the intensity profiles for columns
            for i, col_profile in enumerate(col_profiles):
                x_vals = range(len(col_profile))
                label = f"Column {i + 1}"
                self.plot_widget.plot(x_vals, col_profile, label=label)

            # Update the plot
            self.plot_widget.update_plot()

            # Update status
            self.status_label.setText("Automatic intensity profiles plotted successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    # HELP MENU COMMANDS

    def help(self):
        # Get the absolute path to the user_manual.md file
        user_manual_path = os.path.abspath("C:\\Users\\Josh\\Documents\\PhotoAnalyzer\\docs\\user_manual.md")

        # Create a new window for the user manual
        help_window = tk.Toplevel(self.window)
        help_window.title("User Manual")

        # Create a text widget to display the user manual content
        text_widget = tk.Text(help_window, wrap=tk.WORD, width=80, height=30)
        text_widget.pack(fill=tk.BOTH, expand=True)

        try:
            # Open and read the user_manual.md file
            with open(user_manual_path, "r", encoding="utf-8") as file:
                user_manual_content = file.read()

            # Insert the content into the text widget
            text_widget.insert("1.0", user_manual_content)
        except FileNotFoundError:
            # If the file is not found, display an error message
            text_widget.insert("1.0", "User manual not found!")

        # Disable text editing in the text widget
        text_widget.config(state=tk.DISABLED)

        # Create a link to open the user manual in the default web browser
        def open_in_browser(event):
            webbrowser.open(user_manual_path)

        link_label = tk.Label(help_window, text="Open in Browser", cursor="hand2", fg="blue")
        link_label.pack(pady=5)
        link_label.bind("<Button-1>", open_in_browser)

    # TOOLBAR COMMANDS

    def selectLineTool(self):
        if self.tool:
            self.window.toolbar.recttoolButton.config(relief=tk.RAISED)
            self.window.toolbar.pointtoolButton.config(relief=tk.RAISED)
        self.tool = 'LINE'
        self.window.toolbar.linetoolButton.config(relief=tk.SUNKEN)
        self.useTool()

    def selectRectTool(self):
        if self.tool:
            self.window.toolbar.linetoolButton.config(relief=tk.RAISED)
            self.window.toolbar.pointtoolButton.config(relief=tk.RAISED)
        self.tool = 'RECT'
        self.window.toolbar.recttoolButton.config(relief=tk.SUNKEN)
        self.useTool()

    def selectPointTool(self):
        if self.tool:
            self.window.toolbar.linetoolButton.config(relief=tk.RAISED)
            self.window.toolbar.recttoolButton.config(relief=tk.RAISED)
        self.tool = 'POINT'
        self.window.toolbar.pointtoolButton.config(relief=tk.SUNKEN)
        self.useTool()

    def useTool(self):
        self.Rect = widgets.Rectangle(0, 0, 0, 0)
        self.P1 = widgets.Point(0, 0)
        self.P2 = widgets.Point(0, 0)

        if self.file_is_open:
            self.imagefile.background.bind("<Button-1>", self.Draw1)
            self.imagefile.background.bind("<B1-Motion>", self.Draw2)
            self.imagefile.background.bind("<ButtonRelease-1>", self.Draw3)

    def Draw1(self, event):
        self.clicked = True

        # Coordinates
        self.P1.x = event.x
        self.P1.y = event.y
        self.P2.x = event.x
        self.P2.y = event.y

        if self.imagefile.background.find_withtag("line"):
            self.imagefile.background.delete("line", "aline")
        elif self.imagefile.background.find_withtag("rect"):
            self.imagefile.background.delete("rect")

        if self.tool != "POINT":
            self.imagefile.background.delete("point")
            self.all_points.clear()

        if self.tool == "LINE":
            self.linecoords = (self.P1, self.P2)

    def Draw2(self, event):
        if self.tool != "POINT":
            self.imagefile.background.delete("line", "aline", "rect")

        if self.clicked:
            self.P2.x = event.x
            self.P2.y = event.y
            if self.tool == "LINE":
                self.imagefile.background.create_line(self.P1.x, self.P1.y, self.P2.x, self.P2.y,
                                                 fill=self.color, width=1, tags="line")
                self.imagefile.background.create_line(self.P1.x, self.P1.y, self.P2.x, self.P2.y,
                                                 fill=self.color, width=self.linewidth,
                                                 stipple="gray50", tags="aline")
                self.linecoords = (self.P1, self.P2)
            if self.tool == "RECT":
                if self.P1.get_point_tuple() != (event.x, event.y):
                    self.imagefile.background.create_rectangle(self.P1.x, self.P1.y, self.P2.x, self.P2.y,
                                                          outline=self.color, tags="rect")
                if self.P1.x > self.P2.x:
                    self.Rect.x = self.P2.x
                    self.Rect.width = self.P1.x - self.P2.x
                else:
                    self.Rect.x = self.P1.x
                    self.Rect.width = self.P2.x - self.P1.x
                if self.P1.y > self.P2.y:
                    self.Rect.y = self.P2.y
                    self.Rect.height = self.P1.y - self.P2.y
                else:
                    self.Rect.y = self.P1.y
                    self.Rect.height = self.P2.y - self.P1.y

    def Draw3(self, event):
        if self.tool != "POINT":
            self.imagefile.background.delete("line", "aline", "rect")

        if self.clicked:
            self.P2.x = event.x
            self.P2.y = event.y
            if self.tool == "LINE":
                self.imagefile.background.create_line(self.P1.x, self.P1.y, self.P2.x, self.P2.y, fill=self.color,
                                                 width=1, tags="line")
                self.imagefile.background.create_line(self.P1.x, self.P1.y, self.P2.x, self.P2.y, fill=self.color,
                                                 width=self.linewidth, stipple="gray50", tags="aline")
                self.linecoords = (self.P1, self.P2)
                self.clicked = False
            if self.tool == "RECT":
                self.imagefile.background.create_rectangle(self.P1.x, self.P1.y, self.P2.x, self.P2.y,
                                                      outline=self.color, tags="rect")
            if self.tool == "POINT":
                self.P1 = self.P2
                self.all_points.append(self.P1.get_point_tuple())
                self.imagefile.background.create_oval(self.P1.x-3, self.P1.y-3, self.P2.x+3, self.P2.y+3, fill=self.color,
                                                 tags="point")
                self.clicked = False

    # MENU CREATION

    # Create the menus for the application window
    def create_menus(self):
        self.menubar = tk.Menu(self.window)

        # File menu
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open...", command=self.open_image, accelerator="Ctrl+O")
        self.filemenu.add_command(label="Save", command=self.save_image, accelerator="Ctrl+S")
        self.filemenu.add_command(label="Save As...", command=self.save_image_as)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=widgets.ExitApplication, accelerator="Ctrl+Q")
        self.filemenu.entryconfig("Save", state="disabled")
        self.filemenu.entryconfig("Save As...", state="disabled")
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # Edit menu
        editmenu = tk.Menu(self.menubar, tearoff=0)
        editmenu.add_command(label="Clear", command=self.clear, accelerator="Ctrl+F")
        editmenu.add_separator()

        # Adjust menu in edit menu
        adjustmenu = tk.Menu(editmenu, tearoff=0)
        adjustmenu.add_command(label="Line Width", command=self.line_width)
        editmenu.add_cascade(label="Adjust", menu=adjustmenu)
        self.menubar.add_cascade(label="Edit", menu=editmenu)

        # Image menu
        imagemenu = tk.Menu(self.menubar, tearoff=0)
        imagemenu.add_command(label="Crop", command=self.crop_image)
        imagemenu.add_command(label="Set Scale...", command=self.set_scale)
        imagemenu.add_command(label="Rotate", command=self.rotate_image, state='disabled')
        self.menubar.add_cascade(label="Image", menu=imagemenu)

        # Analyze menu
        self.table = None
        self.table_exists = False

        analyzemenu = tk.Menu(self.menubar, tearoff=0)
        analyzemenu.add_command(label="Measure", command=self.measure)
        analyzemenu.add_command(label="Automatic (Computer Generated) Profile", command=self.plot_automatic_profile) #deprecated until method is added to app.py
        analyzemenu.add_command(label="Manual Profile", command=self.plot_manual_profile)
        #analyzemenu.add_command(label="Generate Voronoi Diagram", command=VoronoiDisplay) #deprecated until method is added to app.py
        self.menubar.add_cascade(label="Analyze", menu=analyzemenu)

        # Help menu
        helpmenu = tk.Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=self.help)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        self.window.config(menu=self.menubar)

    # Create the toolbar for the application window
    def create_toolbar(self):
        self.window.toolbar = tk.Frame(self.window, bd=1, relief=tk.FLAT)

        # Icons go here
        linetoolimg = ImageTk.PhotoImage(Image.open("C:\\Users\\Josh\\Documents\\PhotoAnalyzer\\gui\\resources\\linetoolimg.png"), master=self.window)
        recttoolimg = ImageTk.PhotoImage(Image.open("C:\\Users\\Josh\\Documents\\PhotoAnalyzer\\gui\\resources\\recttoolimg.png"), master=self.window)
        pointtoolimg = ImageTk.PhotoImage(Image.open("C:\\Users\\Josh\\Documents\\PhotoAnalyzer\\gui\\resources\\pointtoolimg.png"), master=self.window)

        self.window.toolbar.linetoolButton = tk.Button(self.window.toolbar, image=linetoolimg,
                                                relief=tk.RAISED, command=self.selectLineTool)
        self.window.toolbar.linetoolButton.image = linetoolimg
        self.window.toolbar.linetoolButton.pack(side=tk.LEFT)

        self.window.toolbar.recttoolButton = tk.Button(self.window.toolbar, image=recttoolimg,
                                                relief=tk.RAISED, command=self.selectRectTool)
        self.window.toolbar.recttoolButton.image = recttoolimg
        self.window.toolbar.recttoolButton.pack(side=tk.LEFT)

        self.window.toolbar.pointtoolButton = tk.Button(self.window.toolbar, image=pointtoolimg,
                                                relief=tk.RAISED, command=self.selectPointTool)
        self.window.toolbar.pointtoolButton.image = pointtoolimg
        self.window.toolbar.pointtoolButton.pack(side=tk.LEFT)

        self.window.toolbar.pack(side=tk.TOP, fill=tk.X)

        
    # Create the infobar for the application window
    def create_infobar(self):
        self.window.infobar = tk.Frame(self.window, bd=1, relief=tk.FLAT)
        self.window.infobar.info = tk.Label(self.window.infobar, text=self.INFO, anchor=tk.NW, justify=tk.LEFT)
        self.window.infobar.info.pack(side=tk.LEFT, padx=1, pady=1)
        self.window.infobar.pack(side=tk.TOP, fill=tk.X)

if __name__ == "__main__":
    app = PhotoAnalyzerApp()
