import numpy as np
import skimage.measure
import math
import os
import sys
sys.path.append('./../gui')
from gui import widgets
import tkinter as tk


def measure(imagefile, P1, P2, table, table_exists, linecoords, linewidth, all_points, window):
    """
    Measure and display image properties based on points or lines drawn on the image.

    Parameters
    ----------
    imagefile : ImageDisplay
        The ImageDisplay object representing the image on the canvas.
    P1 : Point
        A tuple containing the coordinates of one corner of the cropping rectangle or the starting point of the line.
    P2 : Point
        A tuple containing the coordinates of the opposite corner of the cropping rectangle or the ending point of the line.
    linewidth : int
        The width of the line, used when cropping along a drawn line.
    table_exists : bool
        Flag indicating if the measurement table window already exists.
    ms_table_root : tkinter.Tk
        The root tkinter window for the measurement table.
    all_points : list of tuples
        List containing tuples of points drawn on the image.

    Returns
    -------
    None
    """
   
    if not table_exists:
        ms_table_root = tk.Tk()
    else:
        ms_table_root = window

    msscale = imagefile.msscale
    imscale = imagefile.scalefac

    if imagefile.background.find_withtag("point"):
        if not table_exists:
            table = widgets.MeasurementTable(ms_table_root, "measurements", ["Area", "Mean", "Min", "Max", "X", "Y"])
            table_exists = True
        elif table_exists and ("X" and "Y" not in table.tree["columns"]):
            table._add_header(["X", "Y"])

        for p in all_points:
            x, y = int(p[0] / imscale), int(p[1] / imscale)

            if imagefile.image.mode == "RGB":
                r, g, b = imagefile.image.getpixel(p)
                grayval = '%4.2f' % (0.2126 * r + 0.7152 * g + 0.0722 * b)
            else:
                grayval = imagefile.image.getpixel(p)

            if "Length" == table.tree["columns"][2]:
                table._add_row([0, 0, grayval, grayval, grayval, 0, x, y])
            elif "Length" in table.tree["columns"]:
                table._add_row([0, grayval, grayval, grayval, x, y, 0, 0])
            else:
                table._add_row([0, grayval, grayval, grayval, x, y])

    if imagefile.background.find_withtag("line"):
        pimg = np.asarray(imagefile.image)

        if not table_exists:
            table = widgets.MeasurementTable(ms_table_root, "measurements", ["Area", "Length (%s)" % imagefile.unitlen,
                                                                    "Mean", "Min", "Max",
                                                                    "Angle"])
            table_exists = True
        elif table_exists and ("Length (%s)" % imagefile.unitlen and "Angle") not in table.tree["columns"]:
            table._add_header(["Length (%s)" % imagefile.unitlen, "Angle"])

        p = skimage.measure.profile_line(pimg, linecoords[0].get_point_tuple(), linecoords[1].get_point_tuple(),
                                         linewidth=linewidth)

        angle = '%4.3f' % get_angle((linecoords[0].x + 10, linecoords[0].y), linecoords[0], linecoords[1])
        dist = get_distance(linecoords[0], linecoords[1])

        x = int(linecoords[0].x / imscale)
        y = int(linecoords[0].y / imscale)
        length = '%7.3f' % (dist / (imscale * float(msscale)))
        area = '%4.1f' % (dist * linewidth / (imscale * float(msscale)))
        mean = '%4.2f' % np.mean(p)
        vmin = '%3.2f' % p.min()
        vmax = '%3.2f' % p.max()

        if "X" == table.tree["columns"][5]:
            table._add_row([area, mean, vmin, vmax, x, y, length, angle])
        elif "X" in table.tree["columns"]:
            table._add_row([area, length, mean, vmin, vmax, angle, x, y])
        else:
            table._add_row([area, length, mean, vmin, vmax, angle])

    ms_table_root.protocol("WM_DELETE_WINDOW", table._on_close)

    return table, table_exists

def crop_image(imagefile, P1, P2):
    """
    Crop the image using a rectangle or line drawn on the image.

    Parameters
    ----------
    imagefile : ImageDisplay
        The ImageDisplay object representing the image on the canvas.
    P1 : Point
        A tuple containing the coordinates of one corner of the cropping rectangle or the starting point of the line.
    P2 : Point
        A tuple containing the coordinates of the opposite corner of the cropping rectangle or the ending point of the line.
    linewidth : int
        The width of the line, used when cropping along a drawn line.

    Returns
    -------
    None
    """
    if imagefile.background.find_withtag("line") and P1 != P2:
        angle = get_angle((P1.x + 20, P1.y), P1, P2)
        rotated_image = imagefile.image.rotate(-angle)

        P1 = rotate((rotated_image.width / 2, rotated_image.height / 2), P1, angle)
        P2 = rotate((rotated_image.width / 2, rotated_image.height / 2), P2, angle)

        scale = imagefile.image.size[0] / imagefile.background.winfo_reqwidth()
        P1 = widgets.Point(P1.x * scale, P1.y * scale)
        P2 = widgets.Point(P2.x * scale, P2.y * scale)

        cropped_img = rotated_image.crop((P1.x, P1.y, P2.x, P2.y))
        cropped_path = os.path.dirname(imagefile.imagepath) + "/cropped." + imagefile.image.format.lower()
        cropped_img.save(cropped_path)

        imagefile.change_image(cropped_path)

    elif imagefile.background.find_withtag("rect") and P1 != P2:
        scale = imagefile.image.size[0] / imagefile.background.winfo_reqwidth()
        P1 = widgets.Point(P1.x * scale, P1.y * scale)
        P2 = widgets.Point(P2.x * scale, P2.y * scale)

        cropped_img = imagefile.image.crop((P1.x, P1.y, P2.x, P2.y))
        cropped_path = os.path.dirname(imagefile.imagepath) + "/cropped." + imagefile.image.format.lower()
        cropped_img.save(cropped_path)
        imagefile._change_image(cropped_path, cropping=True)

        imagefile.background.delete("rect")


def get_angle(a, b, c):
    """
    Calculate the angle between three points.

    Parameters
    ----------
    a : Point
        A tuple containing the coordinates of the reference point.
    b : Point
        A tuple containing the coordinates of one point.
    c : Point
        A tuple containing the coordinates of another point.

    Returns
    -------
    Float
        The angle between the three points in degrees.
    """
    ang = math.degrees(math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a[1] - b.y, a[0] - b.x))
    return -ang if ang < 0 else ang


def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    Parameters
    ----------
    origin : Point
        A tuple containing the coordinates of the origin point for rotation.
    point : Point
        A tuple containing the coordinates of the point to be rotated.
    angle : float
        The angle of rotation in radians.

    Returns
    -------
    Point
        The new coordinates of the rotated point.
    """
    ox, oy = origin
    px, py = point.x, point.y
    angle = math.radians(angle)
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return widgets.Point(int(qx), int(qy))


def set_scale(imagefile, window, distance):
    """
    Prompt the user to get input for the image scale.

    Parameters
    ----------
    imagefile : ImageDisplay
        The ImageDisplay object representing the image on the canvas.
    window : tkinter.Tk
        The root tkinter window for the application.

    Returns
    -------
    None
    """
    scale_prompt = widgets.ScalePrompt(window, distance)
    imagefile.knowndist, imagefile.unitlen, imagefile.msscale = scale_prompt.get_scale_properties()

def rotate_image(window):
    """
    Prompt the user to get input for image rotation.

    Parameters
    ----------
    window : tkinter.Tk
        The root tkinter window for the application.

    Returns
    -------
    None
    """
    rotate_prompt = widgets.RotatePrompt(window)

def get_distance(p1, p2):
    """
    Calculate the distance between two points.

    Parameters
    ----------
    p1 : Point
        A tuple containing the coordinates of one end-point of the line.
    p2 : Point
        A tuple containing the coordinates of the other end-point of the line.

    Returns
    -------
    Float
        Distance between the two points.
    """
    return np.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)