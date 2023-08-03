import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import win32api
import os

class ImageDisplay(tk.Frame):
    def __init__(self, master, impath, *pargs):
        tk.Frame.__init__(self, master, *pargs)
        
        monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0,0)))
        work_area = monitor_info.get("Work")
        self.screensize = (work_area[2], work_area[3]-106)
        
        self.knowndist = None
        self.unitlen = "pix"
        self.scalefac = 1
        self.msscale = 1
        self.INFO = None
        
        self._display_image(master, impath, self.screensize)
        
        self.background.bind('<Enter>', self.display_mouse_coords)
        self.background.bind('<Leave>', self._display_INFO)
        
    def _change_image(self, new_path, cropping=False):
        self._display_image(self.master, new_path, self.screensize, change=True, cropping=cropping)

    def _display_image(self, master, impath, screensize, change=False, cropping=False):
        if change:
            self.background.delete("image", "line", "aline", "point", "rect")
        if change and not cropping:
            self.knowndist = None
            self.unitlen = "pix"
            self.scalefac = 1
            self.msscale = 1

        self.imagepath = impath
        self.image = Image.open(impath)
        self.pix = self.image.load()
        self.img_copy = self.image.copy()

        self.img_copy.thumbnail(screensize)
        self.scalefac = self.img_copy.size[0] / self.image.size[0]  #scale of tk window image size to actual image pixel size

        self.background_image = ImageTk.PhotoImage(self.img_copy)
        if not change:
            self.background = tk.Canvas(
                master, width=self.img_copy.width, height=self.img_copy.height, cursor="cross"
            )

        self.INFO = os.path.basename(self.imagepath) + ' ({:3.1f}%)'.format(self.scalefac * 100) + '; %dx%d' % (
        self.image.size[0], self.image.size[1])
        master.infobar.info.config(text=self.INFO)

        self.displayedimg = self.background.create_image(
            self.background_image.width() / 2, self.background_image.height() / 2,
            image=self.background_image, tags="image"
        )

        self.background.pack(fill=tk.BOTH)
        master.geometry("%dx%d" % (self.img_copy.size[0], self.img_copy.size[1]))

        self.background.height = self.background.winfo_reqheight()
        self.background.width = self.background.winfo_reqwidth()

        self.scale = self.image.size[0] / self.background.winfo_reqwidth()

        master.maxsize(self.img_copy.size[0], self.img_copy.size[1] + 56)

    def display_mouse_coords(self, event):
        self.funcid = self.background.bind('<Motion>', self.change_text)
    
    def change_text(self, event):
        wx = event.x
        wy = event.y
        txt = txt = self.INFO +";\tx="+str(wx)+"\ty="+str(wy)+"\tValue="+str(self.pix[wx-1,wy-1])
        self.master.infobar.info.config(text = txt)
        
    def _display_INFO(self, event):
        self.master.infobar.info.config(text = self.INFO)
        if hasattr(self, "funcid"):
            self.background.unbind('<Motion>', self.funcid)