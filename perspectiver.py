import cv2
import numpy as np



def perspective_with_scaling(image, pts_src, max_width=1000, max_height=500):
    if image is None:
        # TODO opis błędu
        return


    print("=== Wczytane punkty ===:")
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
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)

    return warped