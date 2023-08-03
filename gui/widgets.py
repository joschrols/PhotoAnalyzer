import tkinter as tk
from tkinter import ttk
import numpy as np
import math
from PIL import ImageOps
import skimage.measure
import matplotlib.figure
import matplotlib.backends.backend_tkagg
import astropy.modeling.models
import astropy.modeling.fitting
import peakutils
from scipy.integrate import quad
import os
import tkinter.messagebox
import tkinter.filedialog


class ExitApplication:
    def __init__(self, master):
        self.master = master

    def exit_with_confirmation(self):
        # Check if any frames are open with items that haven't been saved (e.g., images, tables, plots, etc.)
        # For demonstration purposes, we assume that there's an `is_unsaved_changes()` method in the ImageDisplay class
        if hasattr(self.master, 'imagefile') and self.master.imagefile.is_unsaved_changes():
            # Display warning that items have not been saved
            msg = "Some changes have not been saved. Do you want to exit without saving?"
            if tk.messagebox.askyesno("Exit Confirmation", msg):
                self.master.destroy()
        else:
            # If all frame items have been saved, destroy the application window
            self.master.destroy()

    def check_image_open(self):
        # Assuming `window.FILE_IS_OPEN` is only set by the `Open()` method in main.py
        if hasattr(self.master, 'file_is_open') and self.master.file_is_open:
            return True
        return False

class ScalePrompt(tk.Frame):
    def __init__(self, master, distance):
        self.master = tk.Tk()
        super().__init__(self.master)
        self.distance = distance #/ master.scalefac
        self.returnflag = False

        # Set a label for the entry that displays the distance of the line drawn
        pix_distance_label = tk.Label(self.master, text="Distance in pixels:")
        #pix_distance_label.grid(row=0)
        pix_distance_label.pack()

        # Set a label for the entry that reads user input for the distance of the screen in the image
        known_distance_label = tk.Label(self.master, text="Known distance:")
        known_distance_label.grid(row=1)
        #known_distance_label.pack()

        # Set a label for the entry that reads user input for the unit of length of the known distance measurement
        unit_label = tk.Label(self.master, text="Unit of length:")
        unit_label.grid(row=2)
        #unit_label.pack()

        # Create entry boxes to read user input and organize into rows/columns
        self.entry1 = tk.Entry(self.master)
        self.entry2 = tk.Entry(self.master)
        self.entry3 = tk.Entry(self.master)

        self.entry1.grid(row=0, column=1)
        self.entry2.grid(row=1, column=1)
        self.entry3.grid(row=2, column=1)
        # self.entry1.pack()
        # self.entry2.pack()
        # self.entry3.pack()

        # Display the passed distance parameter formatted to 4 decimal points
        self.entry1.insert(0, "{:.4f}".format(self.distance))

        # Create a "Set Scale" button that quits the prompt mainloop and calculates the scale of the image from user input
        button1 = tk.Button(self.master, text='Set Scale', command=self.set_scale)
        button1.grid(row=4, column=0, pady=4, padx=4)
        #button1.pack(pady=4, padx=4)

        button2 = tk.Button(self.master, text='Cancel', command=self.cancel)
        button2.grid(row=4, column=1, pady=4, padx=4)
        #button2.pack(pady=4, padx=4)

    def set_scale(self):
        if self.returnflag:
            self.known_distance = self.distance
            self.unit_length = 'None'
            self.scale = 1
            self.master.destroy()
            return None

        # Get the user inputs from the entries
        self.known_distance = float(self.entry2.get())
        self.unit_length = self.entry3.get()

        # Calculate the scale of the image in pixels per unit length
        self.scale = self.distance / self.known_distance
        # print(f'Scale is {self.scale} pixels/{self.unit_length}.')

        # Destroy the prompt display
        self.master.destroy()

    def get_scale_properties(self):
        if hasattr(self, "known_distance") and hasattr(self, "unit_length") and hasattr(self, "scale"):
            pass
        else:
            self.known_distance = self.distance
            self.unit_length = 'None'
            self.scale = 1
        return self.known_distance, self.unit_length, self.scale

    def cancel(self):
        self.returnflag = True
        self.master.quit()

class RotatePrompt(tk.Frame):
    def __init__(self, master, angle=None):
        super().__init__(master)
        self.master = master
        self.angle = angle
        self.returnflag = False

        if self.master.background.find_withtag("line"):
            self.angle = self.get_angle()

        else:
            self.angle = self.prompt_for_angle()

    def get_angle(self):
        P1, P2 = self.get_line_endpoints()
        angle = self.calculate_angle(P1, P2)
        return angle

    def prompt_for_angle(self):
        self.angle_label = tk.Label(self.master, text="Enter rotation angle:")
        self.angle_label.grid(row=0)

        self.angle_entry = tk.Entry(self.master)
        self.angle_entry.grid(row=0, column=1)

        self.ok_button = tk.Button(self.master, text='OK', command=self.set_angle)
        self.ok_button.grid(row=1, column=0, pady=4, padx=4)

        self.cancel_button = tk.Button(self.master, text='Cancel', command=self.cancel)
        self.cancel_button.grid(row=1, column=1, pady=4, padx=4)

        self.master.mainloop()

        if self.returnflag:
            self.angle = "_angle"
            self.master.destroy()
            return self.angle

        # Get the user input from the entry
        self.angle = float(self.angle_entry.get())
        self.master.destroy()

    def set_angle(self):
        if not self.angle:
            self.angle = self.get_angle()
        else:
            self.returnflag = True
        self.master.quit()

    def cancel(self):
        self.returnflag = True
        self.master.quit()

    def get_line_endpoints(self):
        line_items = self.master.background.find_withtag("line")
        P1 = Point(self.master.background.coords(line_items[0])[0], self.master.background.coords(line_items[0])[1])
        P2 = Point(self.master.background.coords(line_items[0])[2], self.master.background.coords(line_items[0])[3])
        return P1, P2

    def calculate_angle(self, P1, P2):
        ang = math.degrees(math.atan2(P2.y - P1.y, P2.x - P1.x))
        return -ang if ang < 0 else ang

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_point_array(self):
        return np.asarray([self.x, self.y])

    def get_point_tuple(self):
        return (self.x, self.y)
    
class Peak:
    def __init__(self, c, h, a, fwhm, hwhm, peakid, rcs):
        self.center = c
        self.height = h
        self.area = a
        self.fwhm = fwhm
        self.hwhm = hwhm
        self.id = peakid
        self.rcs = rcs

class Rectangle:
    def __init__(self, _Tp_x, _Tp_y, _Tp_width, _Tp_height):
        self.x = _Tp_x
        self.y = _Tp_y
        self.width = _Tp_width
        self.height = _Tp_height
    
class PlotWidget(tk.Tk):
    def __init__(self, data, imagefile, *pargs):
        super().__init__()
        self.data = np.asarray(data)
        self.data_x = np.linspace(0, len(data) / imagefile.msscale, len(data))  #Note: fix imagefile not being defined
        self.data_y = self.data
        self.databackup = self.data.copy()

        # Display values for troubleshooting
        # print("PLOT VALUES:")
        # print(f"\tMOD={1.0 / imagefile.msscale} {imagefile.unitlen}/pix")
        # print("\tNUM OF UNSCALED DATA=", len(self.data))
        # print("\tTRUE SIZE OF IMAGE=", imagefile.image.size)
        # print("\tDISPLAY SIZE OF IMAGE=", imagefile.img_copy.size)
        # print("\tMAX VAL OF UNSCALED DATA=", max(self.data))
        # print("\tMAX VAL OF SCALED DATA=", max(self.data_x))

        # Initialize and format menu and toolbar
        self.mainmenu = tk.Menu(self)
        self.filemenu = tk.Menu(self.mainmenu, tearoff=0)
        self.filemenu.add_command(label="Save as Image...", command=self.save_as_image)
        self.filemenu.add_command(label="Reset", command=self.reset)
        self.mainmenu.add_cascade(label="File", menu=self.filemenu)

        self.datamenu = tk.Menu(self.mainmenu, tearoff=0)
        self.datamenu.add_command(label="Export As...", command=self.export_as)
        self.datamenu.add_command(label="Table", command=self.show_table)

        self.blhandlingmenu = tk.Menu(self.datamenu, tearoff=0)
        self.blhandlingmenu.add_command(label="Add Baseline", command=self.add_baseline)
        self.blhandlingmenu.add_command(label="Clear Baseline", command=self.clear_baseline, state='disabled')
        self.blhandlingmenu.add_command(label="Subtract Baseline", command=self.sub_baseline)
        self.datamenu.add_cascade(label="Baseline Handling...", menu=self.blhandlingmenu)
        self.mainmenu.add_cascade(label="Data", menu=self.datamenu)

        self.fitmenu = tk.Menu(self.mainmenu, tearoff=0)
        self.fitmenu.add_command(label="Guess Peak", command=self.guess_peak)
        self.fitmenu.add_command(label="Export Peak Parameters", command=self.export_peaks)
        self.mainmenu.add_cascade(label="Fit", menu=self.fitmenu)
        self.config(menu=self.mainmenu)

        self.toolbar = tk.Frame(self, bd=1, relief=tk.FLAT)
        self.toolbar.blmode = tk.Button(self.toolbar, relief=tk.RAISED, text="Baseline Mode", command=self.bl_mode)
        self.toolbar.blmode.pack(side=tk.LEFT)
        self.toolbar.stripbg = tk.Button(self.toolbar, relief=tk.RAISED, text="Strip Background", command=self.sub_baseline)
        self.toolbar.stripbg.pack(side=tk.LEFT)
        self.toolbar.peakmode = tk.Button(self.toolbar, relief=tk.RAISED, text="Add-Peak Mode", command=self.ap_mode)
        self.toolbar.peakmode.pack(side=tk.LEFT)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Initialize data figure and canvas
        self.fig = matplotlib.figure.Figure(figsize=(8, 6), dpi=100)
        self.plot = self.fig.add_subplot(111)
        self.fig.main, = self.plot.plot(self.data_x, self.data, 'go', markersize=1)
        self.plot.axhline(0, color='gray', linestyle='--', markersize=1)
        self.plot.axvline(0, color='gray', linestyle='--', markersize=1)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
        self.navbar = matplotlib.backends.backend_tkagg.NavigationToolbar2Tk(self.canvas, self)
        self.navbar.update()
        self.canvas.get_tk_widget().pack()

        self.resizable(0, 0)
        self.mainloop()

    def save_as_image(self):
        ftypes = (("", "*"), ("JPEG", "*.jpg"), ("PNG", "*.png"))
        temp = tk.filedialog.asksaveasfile(defaultextension="", filetypes=ftypes)
        if not temp:
            return
        filename, ext = os.path.splitext(temp.name)
        if ("", ext) not in ftypes:
            tk.messagebox.showerror(title='File Extension Error', message="Unknown file extension '%s' used." % ext)
            temp.close()
            os.remove(temp.name)
        else:
            self.fig.savefig(temp.name)
            temp.close()

    def reset(self):
        self.fig.clf()
        self.plot = self.fig.add_subplot(111)
        self.data = self.databackup
        self.plot.plot(self.data_x, self.data, 'go', markersize=1)
        self.plot.axhline(0, color='gray', linestyle='--', markersize=1)
        self.plot.axvline(0, color='gray', linestyle='--', markersize=1)
        self.canvas.draw()

    def export_as(self):
        temp = tk.filedialog.asksaveasfile(defaultextension="", filetypes=(("", "*"), ("CSV", "*.csv"), ("TXT", "*.txt")))

        if not temp:
            return

        filename, ext = os.path.splitext(temp.name)

        export_data = list()
        if hasattr(self, 'peakdata'):
            hdrs = list(self.peakdata[0].__dict__.keys())
            export_data.append([hdrs[5], hdrs[0], hdrs[1], hdrs[2], hdrs[3], hdrs[4], hdrs[6]])
            for p in self.peakdata:
                vals = list()
                for attr in export_data[0]:
                    vals.append(getattr(p, attr))
                export_data.append(np.asarray(vals))
        else:
            export_data.append(['x (pixel)', 'y (intensity)'])
            x = np.arange(0, len(self.data))
            for i in range(len(self.data)):
                export_data.append([x[i], self.data[i]])

        if ext == '.csv':
            np.savetxt("%s.csv" % filename, np.asarray(export_data), delimiter=", ", fmt='%s')
        elif ext == '.txt':
            np.savetxt("%s.txt" % filename, np.asarray(export_data), delimiter=", ", fmt='%s')
        else:
            tk.messagebox.showerror(title='File Extension Error', message="Unknown file extension '%s' used." % ext)
            temp.close()
            os.remove(temp.name)
            return

        temp.close()

    def show_table(self):
        root = tk.Tk()
        if hasattr(self, 'peakdata'):
            data_table = MeasurementTable(root, 'Peak Data', [''] + list(self.peakdata[0].__dict__.keys()))
            for p in self.peakdata:
                data_table._add_row(list(p.__dict__.values()))
        else:
            data_table = MeasurementTable(root, 'Intensity Profile Data', ['', 'Intensity'])
            for p in self.data:
                data_table._add_row([p])
        root.mainloop()

    def add_baseline(self):
        self.baseline = peakutils.baseline(self.data)
        self.fig.bl, = self.plot.plot(self.data_x, self.baseline, 'r-')
        self.canvas.draw()
        self.blhandlingmenu.entryconfig("Clear Baseline", state='normal')

    def clear_baseline(self):
        self.fig.bl.remove()
        delattr(self, 'baseline')
        self.canvas.draw()
        self.blhandlingmenu.entryconfig("Clear Baseline", state='disabled')

    def sub_baseline(self):
        if not hasattr(self, 'baseline'):
            tk.messagebox.showerror("Error", "Baseline has not been set.")
        else:
            self.blhandlingmenu.entryconfig("Clear Baseline", state='disabled')
            self.fig.clf()
            self.plot = self.fig.add_subplot(111)
            self.data = self.data - self.baseline
            self.plot.plot(self.data_x, self.data, 'go', markersize=1)
            ylim = self.plot.get_ylim()
            locs = self.plot.get_yticks()
            ymin = int(min(ylim) - 1)
            self.plot.set_yticks([ymin] + locs)
            self.plot.set_ylim(ymin, max(locs))
            self.plot.axhline(0, color='gray', linestyle='--', markersize=1)
            self.plot.axvline(0, color='gray', linestyle='--', markersize=1)
            self.canvas.draw()
            delattr(self, 'baseline')

    def guess_peak(self):
        self.peakindices = peakutils.indexes(self.data, thres=0.3, min_dist=40)
        self.initialvals = peakutils.interpolate(self.data_x, self.data, ind=self.peakindices, width=35)

        lmbasexmax = 0
        fit_list = list()
        extrema_list = list()
        rcs_list = list()
        for i in range(len(self.peakindices)):
            if i == 0:
                llim = 0
            else:
                llim = self.peakindices[i - 1]
            if i == len(self.peakindices) - 1:
                hlim = len(self.data)
            else:
                hlim = self.peakindices[i + 1]

            xmin, xmax = self.find_extrema(self.data, self.peakindices[i], llim, hlim)
            extrema_list.append([xmin, xmax])
            if i == 0:
                lmbasexmax = xmin
            N = xmax - xmin

            # FOR TROUBLESHOOTING
            # print("\n%d_Gaussian" % i)
            # print("Points: ", N)

            xs = np.arange(xmin, xmax)
            ys = self.data[xmin:xmax]
            a = self.data[self.peakindices[i]]
            b = self.initialvals[i]
            c = np.std(self.data[llim:hlim])
            y_err = np.ones(N) * c

            model_gauss = astropy.modeling.models.Gaussian1D(amplitude=a, mean=b, fixed={'amplitude': True})
            fitter_gauss = astropy.modeling.fitting.LevMarLSQFitter()
            best_fit_gauss = fitter_gauss(model_gauss, xs, ys, weights=1.0 / (2.0 * y_err ** 2))
            # cov_diag = np.diag(fitter_gauss.fit_info['param_cov'])
            fit_list.append(best_fit_gauss)
            rcs = self.calc_reduced_chi_square(best_fit_gauss(xs), xs, ys, y_err, N, 2)
            rcs_list.append(rcs)

            self.plot.plot(self.data_x, best_fit_gauss(self.data_x), 'r-')
            self.plot.plot(self.initialvals[i], self.data[self.peakindices[i]], color='black', marker='o', markersize=3)
            self.canvas.draw()

        self.peakparams = np.asarray(fit_list)

        mean_intensity = np.mean(self.data)
        cont = np.where(self.data > mean_intensity, mean_intensity, self.data)
        linfitter = astropy.modeling.fitting.LinearLSQFitter()
        poly_cont = linfitter(astropy.modeling.models.Polynomial1D(1), self.data_x, cont)

        for i in range(len(fit_list)):
            if i == 0:
                fit_combo = fit_list[i]
            else:
                fit_combo += fit_list[i]

        fit_combo += poly_cont

        fitter = astropy.modeling.fitting.LevMarLSQFitter()
        fitted_model = fitter(fit_combo, self.data_x, self.data, maxiter=len(self.data_x))
        fit_y = fitted_model(self.data_x)
        self.plot.plot(self.data_x, fit_y, 'y-')

        lmb = np.polyfit(np.arange(0, lmbasexmax), fit_y[:int(lmbasexmax)], 1)
        lmbase = np.poly1d(lmb)

        self.plot.plot(self.data_x, lmbase(self.data_x) - 1, 'r--')
        self.canvas.draw()

        self.peakdata = list()
        for i in range(len(fit_list)):
            xmin, xmax = extrema_list[i]
            g = fit_list[i]
            xset = np.linspace(0, len(self.data), num=int(len(self.data) / .01))
            gdata = g(xset)
            c = self.initialvals[i]
            h = max(gdata)
            a = quad(g, xmin, xmax)[0]
            fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0)) * g.stddev.value
            hwhm = fwhm / 2.0

            pdata = Peak(c, h, a, fwhm, hwhm, i + 1, rcs_list[i])
            self.peakdata.append(pdata)

    def export_peaks(self):
        if hasattr(self, 'peakparams'):
            temp = tk.filedialog.asksaveasfile(defaultextension="", filetypes=(("", "*"), ("CSV", "*.csv"), ("TXT", "*.txt")))
            if not temp:
                return
            filename, ext = os.path.splitext(temp.name)

            export_data = list()
            export_data.append(np.asarray(self.peakparams[0].param_names))
            for parset in self.peakparams:
                export_data.append([getattr(parset, attr).value for attr in parset.param_names])
            export_data = np.asarray(export_data)

            if ext == '.csv':
                np.savetxt("%s.csv" % filename, np.asarray(export_data), delimiter=", ", fmt='%s')
            elif ext == '.txt':
                np.savetxt("%s.txt" % filename, np.asarray(export_data), delimiter=", ", fmt='%s')
            else:
                tk.messagebox.showerror(title='File Extension Error', message="Unknown file extension '%s' used." % ext)
                temp.close()
                os.remove(temp.name)
                return

            temp.close()
        else:
            tk.messagebox.showerror(title="Error", message="No peaks found.")

    def bl_mode(self):
        self.toolbar.blmode.config(relief=tk.SUNKEN)
        self.toolbar.peakmode.config(relief=tk.RAISED)
        self.mode = 'blMode'
        self.N = 0
        self.blpoints = list()
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.bl_point)

    def bl_point(self, event):
        x, y = event.xdata, event.ydata
        self.N += 1
        self.blpoints.append((x, y))
        self.get_baseline_eq()

    def get_baseline_eq(self):
        xs = np.asarray(self.blpoints)[:, 0]
        ys = np.asarray(self.blpoints)[:, 1]
        coeffs = np.polyfit(xs, ys, self.N - 1)
        poly = np.poly1d(coeffs)
        self.baseline = poly(self.data_x)
        self.plot.plot(xs, ys, 'ro', markersize=3)
        if hasattr(self.fig, 'bl'):
            self.fig.bl.remove()
        self.fig.bl, = self.plot.plot(self.data_x, self.baseline, 'r--')
        self.canvas.draw()

    def ap_mode(self):
        self.toolbar.blmode.config(relief=tk.RAISED)
        self.toolbar.peakmode.config(relief=tk.SUNKEN)
        self.mode = 'apMode'
        self.peaknum = 0
        self.peaks = list()
        self.pressed = False
        self.fit_list = list()
        self.peakdata = list()
        self.peakID = 1
        self.fig.canvas.mpl_disconnect(self.cid1)
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.set_peak_center)
        self.cid2 = self.fig.canvas.mpl_connect('button_release_event', self.release)

    def set_peak_center(self, event):
        self.pressed = True
        self.peakc = event.xdata
        self.peakh = event.ydata
        self.peakb = 1

        # side 1
        x11 = self.peakc - self.peakb
        y11 = 0
        x12 = self.peakc
        y12 = self.peakh
        xs1 = [x11, x12]
        ys1 = [y11, y12]

        # side 2
        x21 = self.peakc
        y21 = self.peakh
        x22 = self.peakc + self.peakb
        y22 = 0
        xs2 = [x21, x22]
        ys2 = [y21, y22]

        # altitude
        x31 = self.peakc
        y31 = 0
        x32 = self.peakc
        y32 = self.peakh
        xs3 = [x31, x32]
        ys3 = [y31, y32]

        self.fig.peaktriside1, = self.plot.plot(xs1, ys1, color='black', linestyle='--')
        self.fig.peaktriside2, = self.plot.plot(xs2, ys2, color='black', linestyle='--')
        self.fig.peaktriside3, = self.plot.plot(xs3, ys3, color='black', linestyle='--')

        self.fig.canvas.draw()

        self.cid3 = self.fig.canvas.mpl_connect('motion_notify_event', self.draw_peak)

    def draw_peak(self, event):
        if not self.pressed:
            return
        if hasattr(self.fig, 'peaktriside1') or hasattr(self.fig, 'peaktriside2'):
            self.fig.peaktriside1.remove()
            self.fig.peaktriside2.remove()
            self.fig.peaktriside3.remove()
        self.peakh = event.ydata
        self.peakb = abs(self.peakc - event.xdata)
        if self.peakb == 0:
            self.peakb = 1

        # side 1
        x11 = self.peakc - self.peakb
        y11 = 0
        x12 = self.peakc
        y12 = self.peakh
        xs1 = [x11, x12]
        ys1 = [y11, y12]

        # side 2
        x21 = self.peakc
        y21 = self.peakh
        x22 = self.peakc + self.peakb
        y22 = 0
        xs2 = [x21, x22]
        ys2 = [y21, y22]

        # altitude
        x31 = self.peakc
        y31 = 0
        x32 = self.peakc
        y32 = self.peakh
        xs3 = [x31, x32]
        ys3 = [y31, y32]

        self.fig.peaktriside1, = self.plot.plot(xs1, ys1, color='black', linestyle='--')
        self.fig.peaktriside2, = self.plot.plot(xs2, ys2, color='black', linestyle='--')
        self.fig.peaktriside3, = self.plot.plot(xs3, ys3, color='black', linestyle='--')

        self.fig.canvas.draw()

    def release(self, event):
        self.pressed = False

        # Disconnect event binding to prevent unwanted usage of command
        self.fig.canvas.mpl_disconnect(self.cid3)

        # Get x-coord of peak, xmin/xmax of curve, y-coord of peak
        x = self.peakc
        y = self.peakh
        b = self.peakb
        x_vals = np.arange(x - b, x + b)
        xmin = x_vals[0]
        xmax = x_vals[-1]
        y_vals = self.data[int(x_vals[0]):int(x_vals[-1]) + 1]
        c = np.std(y_vals)
        N = len(x_vals)
        y_err = np.ones(N) * c

        # Form Gaussian
        model_gauss = astropy.modeling.models.Gaussian1D(amplitude=y, mean=x, fixed={'amplitude': True})
        fitter_gauss = astropy.modeling.fitting.LevMarLSQFitter()
        best_fit_gauss = fitter_gauss(model_gauss, x_vals, y_vals, weights=1.0 / (2.0 * y_err ** 2))
        self.fit_list.append(best_fit_gauss)
        self.peakparams = np.asarray(self.fit_list)
        rcs = self.calc_reduced_chi_square(best_fit_gauss(x_vals), x_vals, y_vals, y_err, N, 2)

        # Get sum of Gaussian and attach peak ID
        a = quad(best_fit_gauss, xmin, xmax)[0]
        fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0)) * best_fit_gauss.stddev.value
        hwhm = fwhm / 2.0
        pdata = Peak(c, y, a, fwhm, hwhm, self.peakID, rcs)
        self.peakdata.append(pdata)
        self.plot.plot(self.data_x, best_fit_gauss(self.data_x), 'r-')
        self.plot.plot(x, y, color='black', marker='o', markersize=3)
        self.canvas.draw()

        self.peakID += 1

    @staticmethod
    def calc_reduced_chi_square(fitted_y, x, y, y_err, N, n):
        resids = y - fitted_y
        chisq = sum((resids / y_err) ** 2)
        dof = N - n
        rcs = chisq / dof
        return rcs
    @staticmethod
    def find_extrema(data, peak, llim, hlim):
        xmin = peak
        i = peak
        ymin = data[peak]
        while i > llim:
            if data[i] < ymin:
                ymin = data[i]
                xmin = i
            i -= 1
        xmax = peak
        i = peak
        ymin = data[peak]
        while i < hlim:
            if data[i] < ymin:
                ymin = data[i]
                xmax = i
            i += 1
        return (xmin, xmax)
    
class MeasurementTable:
    def __init__(self, master, title, headers):
        self.master = master
        self.master.title(title)

        self.tree = ttk.Treeview(master, columns=headers, show="headings")

        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, anchor=tk.CENTER, width=80)

        self.tree.pack()

    def _add_header(self, headers):
        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, anchor=tk.CENTER, width=80)

    def _add_row(self, values):
        self.tree.insert("", tk.END, values=values)

    def _on_close(self):
        self.master.destroy()
