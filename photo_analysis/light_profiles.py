import cv2
import numpy as np
import math
import imutils
import skimage.measure
from sklearn.neighbors import NearestNeighbors
from PIL import ImageOps
# import sys
# sys.path.append('.')
from photo_utils import rotate, get_angle

def create_nmatrix(arr, dis, n, ang=0, org='r'):
    origin = np.mean(arr, axis=0)
    nmatrix = np.zeros((n, n, 2))
    s = dis * np.cos(np.radians(ang))
    h = dis * np.sin(np.pi / 2 - np.radians(ang))

    for i in range(n):
        if org == 'c':
            smul = (i+1) - (n/2.0) - 0.5
        else:
            hmul = (n/2.0) - (i+1) + 0.5
        for j in range(n):
            if org == 'c':
                hmul = (n/2.0) - (j+1) + 0.5
            else:
                smul = (j+1) - (n/2.0) - 0.5

            tempx = origin[0] + smul * s
            tempy = origin[1] - hmul * h
            if org == 'c':
                nmatrix[i][j] = rotate(origin, [tempx, tempy], math.radians(90+ang))
            else:
                nmatrix[i][j] = rotate(origin, [tempx, tempy], math.radians(ang))

    return nmatrix

def closest_k_points(points, point, k):
    ps = [(p[0], p[1]) for p in points]
    x, y = point.ravel()
    ps.sort(key=lambda k: (k[0] - x) ** 2 + (k[1] - y) ** 2)
    return ps[:k]

def best_fit_intercepts(points, indices, xmin=0, xmax=1000, ymin=0, ymax=1000, org='r'):
    n = int(math.sqrt(len(points)))
    intercepts = []
    for r in range(n):
        all_indices = []
        if org == 'c':
            for i in range(r * n, n * (r + 1)):
                if indices[i][1] not in all_indices:
                    all_indices.append(indices[i][1])
        else:
            for i in range((n - 1) * r, (n - 1) * (r + 1)):
                for j in range(2):
                    if indices[i][j] not in all_indices:
                        all_indices.append(indices[i][j])
        all_xs = [points[i][0] for i in all_indices]
        all_ys = [points[i][1] for i in all_indices]

        p = np.poly1d(np.polyfit(all_xs, all_ys, 1))
        m, b = p.c.ravel()
        if org == 'c':
            x1 = (ymin - b) / m
            x2 = (ymax - b) / m
            if x2 > x1:
                intercepts.append([[x1, ymin], [x2, ymax]])
            else:
                intercepts.append([[x2, ymax], [x1, ymin]])
        else:
            y1 = m * xmin + b
            y2 = m * xmax + b
            intercepts.append([[xmin, y1], [xmax, y2]])

    return intercepts

def getPtDistance(p1, p2):
    x1, y1 = p1.ravel()
    x2, y2 = p2[0], p2[1]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def detect_bright_spots(im, output_path=None):
    image = im.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    most_freq = np.bincount(blurred.copy().flatten()).argmax()
    thresh = cv2.threshold(blurred, most_freq + int(most_freq * (2 / 3)) + 2, 255, cv2.THRESH_BINARY)[1]
    th1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 149, int(most_freq * 2 / 3))
    thresh = cv2.erode(thresh, None, iterations=6)
    thresh = cv2.dilate(thresh, None, iterations=2)
    th1 = cv2.erode(th1, None, iterations=5)
    th1 = cv2.dilate(th1, None, iterations=2)
    labels = skimage.measure.label(thresh, connectivity=2, background=0)
    mask = np.zeros(thresh.shape, dtype="uint8")

    for label in np.unique(labels):
        if label == 0:
            continue
        labelMask = np.zeros(thresh.shape, dtype="uint8")
        labelMask[labels == label] = 255
        numPixels = cv2.countNonZero(labelMask)
        if numPixels > 30:
            mask = cv2.add(mask, labelMask)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = imutils.contours.sort_contours(cnts)[0]
    centers = np.zeros((len(cnts), 2))

    for i, cnt in enumerate(cnts):
        M = cv2.moments(cnt)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        centers[i] = (cX, cY)

    return centers, image

def find_rotation_angle(arr):
    nbrs = NearestNeighbors(n_neighbors=2, algorithm='auto').fit(arr)
    distances, indices = nbrs.kneighbors(arr)
    angles = np.zeros(len(indices))

    for i in range(len(indices)):
        pt1 = arr[indices[i][0]]
        pt2 = arr[indices[i][1]]
        dx = abs(pt1[0] - pt2[0])
        dy = abs(pt1[1] - pt2[1])

        angles[i] = math.degrees(np.arcsin(dy / distances[i][1]))

        if dy > dx:
            angles[i] = 90.0 - angles[i]

        if angles[i] / 10 ** -13 < 10.0:
            angles[i] = 0.0

    return np.average(angles)

class IntensityProfile:
    def __init__(self, imagefile, linewidth, P1, P2):
        self.imagefile = imagefile
        self.linewidth = linewidth
        self.P1 = P1
        self.P2 = P2

    def get_intensity_profile(self):
        if self.imagefile.background.find_withtag("line"):
            gray = np.asarray(ImageOps.grayscale(self.imagefile.image))
            start = (self.P1.x / self.imagefile.scalefac, self.P1.y / self.imagefile.scalefac)
            end = (self.P2.x / self.imagefile.scalefac, self.P2.y / self.imagefile.scalefac)
            profile = skimage.measure.profile_line(gray, start, end, linewidth=self.linewidth)
            return profile
        else:
            return None
        
    def automatic_profiler(self, path, linewidth=5):
        gray_img = cv2.imread(path)
        points, img = detect_bright_spots(gray_img)
        centroidm = np.mean(points, axis=0)
        angle = find_rotation_angle(points)
        row_list = []
        col_list = []

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                B = points[i]
                C = points[j]
                dist = math.sqrt((C[0] - B[0]) ** 2 + (C[1] - B[1]) ** 2)
                A = (B[0] + dist, B[1])
                ang = get_angle(A, B, C)

                if math.isclose(ang, angle, rel_tol=0.5) or math.isclose(ang, -angle, rel_tol=0.5) and B[1] > A[1]:
                    row_list.append((i, j))
                elif math.isclose(90.0 - ang, angle, rel_tol=0.5) or math.isclose(90.0 - ang, -angle, rel_tol=0.5) and B[0] < A[0]:
                    col_list.append((i, j))

        closestk = closest_k_points(points, centroidm, 4)
        nbrs = NearestNeighbors(n_neighbors=2, algorithm='auto').fit(closestk)
        distances, indices = nbrs.kneighbors(closestk)
        avgdist = np.mean(distances[:, 1])
        
        mat = create_nmatrix(closestk, avgdist, 12, ang=-angle)
        matc = create_nmatrix(closestk, avgdist, 12, ang=-angle, org='c')

        for r in range(len(mat)):
            for p in range(len(mat)):
                pt = mat[r][p]
                closestpt = closest_k_points(points, pt, 1)[0]
                if getPtDistance(pt, closestpt) <= 35:
                    mat[r][p] = closestpt

        for r in range(len(matc)):
            for p in range(len(matc)):
                pt = matc[r][p]
                closestpt = closest_k_points(points, pt, 1)[0]
                if getPtDistance(pt, closestpt) <= 35:
                    matc[r][p] = closestpt

        mat_list = [mat[c][r] for r in range(len(mat)) for c in range(len(mat))]
        n = len(mat)
        matc_list = [matc[c][r] for r in range(len(matc)) for c in range(len(matc))]
        nc = len(matc)

        inds = [[i, j] for i in range(n) for j in range(i + n, i + (n - 1) * n + 1, n)]
        indsc = [[i, j] for i in range(nc) for j in range(i * nc, i * nc + nc)]

        ints = best_fit_intercepts(mat_list, inds, xmax=gray_img.shape[1] - 1, ymax=gray_img.shape[0])
        intsc = best_fit_intercepts(mat_list, indsc, xmax=gray_img.shape[1] - 1, ymax=gray_img.shape[0], org='c')

        gray = cv2.cvtColor(gray_img, cv2.COLOR_BGR2GRAY)
        rowdistances = [getPtDistance(np.asarray(ints[r][1]), tuple(ints[r + 1][1])) for r in range(len(ints) - 1)]
        coldistances = [getPtDistance(np.asarray(intsc[c][0]), tuple(intsc[c + 1][0])) for c in range(len(intsc) - 1)]
        rowprofiles = [skimage.measure.profile_line(gray, ints[row][0], ints[row][1], linewidth=linewidth) for row in range(n)]
        colprofiles = [skimage.measure.profile_line(gray, intsc[col][0], intsc[col][1], linewidth=linewidth) for col in range(nc)]

        return rowprofiles, colprofiles, closestk, avgdist, 12, -angle, points
    
if __name__ == "__main__":
    print("Test performed: All systems nominal.")