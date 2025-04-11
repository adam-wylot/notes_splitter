import cv2
import numpy as np
from PyQt5 import QtWidgets
from matplotlib import pyplot as plt


# Lista klikniętych punktów (w oryginalnej skali)
# points = []


# def mouse_callback(event, x, y, flags, param):
#     if event == cv2.EVENT_LBUTTONDOWN:
#         scale = param["scale"]
#         margin = param["margin"]
#         # Przelicz kliknięte współrzędne z obrazu z marginesem do oryginalnego obrazu
#         orig_x = (x - margin) / scale
#         orig_y = (y - margin) / scale
#         orig_point = (int(orig_x), int(orig_y))
#         points.append(orig_point)
#         print(f"Kliknięto punkt (na skali wyświetlania): {(x, y)}; przeliczony: {orig_point}")
#
#
# def order_points(pts):
#     """
#     Porządkuje 4 punkty do kolejności:
#     [top-left, top-right, bottom-left, bottom-right]
#     """
#     # Zamieniamy listę na tablicę NumPy
#     pts = np.array(pts)
#     # Najpierw sortujemy według współrzędnej y (w kolejności rosnącej)
#     sorted_y = pts[np.argsort(pts[:, 1]), :]
#     # Górne dwa punkty
#     top_two = sorted_y[:2]
#     # Dolne dwa punkty
#     bottom_two = sorted_y[2:]
#
#     # Spośród górnych – ten z mniejszym x jest top-left, drugi top-right
#     top_two = top_two[np.argsort(top_two[:, 0]), :]
#     tl, tr = top_two[0], top_two[1]
#
#     # Spośród dolnych – ten z mniejszym x to bottom-left, drugi bottom-right
#     bottom_two = bottom_two[np.argsort(bottom_two[:, 0]), :]
#     bl, br = bottom_two[0], bottom_two[1]
#
#     return np.array([tl, tr, bl, br], dtype="float32")


def perspective_with_scaling(image, pts_src, max_width=1000, max_height=500):
    if image is None:
        # TODO opis błędu
        return

    plt.imshow(image)
    plt.axis('off')  # ukrywa osie (opcjonalnie)
    plt.show()

    # pts_src = np.array(pts, dtype=np.float32)

    # Uporządkuj punkty – automatyczne wykrycie rogów
    #pts_src = order_points(pts)

    print("Punkty po uporządkowaniu:")
    print("Top-left:    ", pts_src[0])
    print("Top-right:   ", pts_src[1])
    print("Bottom-left: ", pts_src[2])
    print("Bottom-right:", pts_src[3])

    # Definiujemy docelowy rozmiar wyprostowanego obrazu
    width_top = np.linalg.norm(pts_src[0] - pts_src[1])
    width_bottom = np.linalg.norm(pts_src[2] - pts_src[3])
    width_target = int(max(width_top, width_bottom))

    height_left = np.linalg.norm(pts_src[0] - pts_src[2])
    height_right = np.linalg.norm(pts_src[1] - pts_src[3])
    height_target = int(max(height_left, height_right))

    # Definiujemy nowe docelowe położenia punktów (przyjmujemy kolejność: top-left, top-right, bottom-left, bottom-right)
    pts_dst = np.float32([
        [0, 0],
        [width_target - 1, 0],
        [0, height_target - 1],
        [width_target - 1, height_target - 1]
    ])

    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped = cv2.warpPerspective(image, M, (width_target, height_target))
    # Jeśli obraz wejściowy był w formacie BGR (czyli wczytany przez cv2.imread), zamieniamy na RGB
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    plt.imshow(warped_rgb)
    plt.axis('off')
    plt.show()
    return warped