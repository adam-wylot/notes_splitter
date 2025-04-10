import cv2
import numpy as np

# Lista klikniętych punktów (w oryginalnej skali)
points = []


def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        scale = param["scale"]
        margin = param["margin"]
        # Przelicz kliknięte współrzędne z obrazu z marginesem do oryginalnego obrazu
        orig_x = (x - margin) / scale
        orig_y = (y - margin) / scale
        orig_point = (int(orig_x), int(orig_y))
        points.append(orig_point)
        print(f"Kliknięto punkt (na skali wyświetlania): {(x, y)}; przeliczony: {orig_point}")


def order_points(pts):
    """
    Porządkuje 4 punkty do kolejności:
    [top-left, top-right, bottom-left, bottom-right]
    """
    # Zamieniamy listę na tablicę NumPy
    pts = np.array(pts)
    # Najpierw sortujemy według współrzędnej y (w kolejności rosnącej)
    sorted_y = pts[np.argsort(pts[:, 1]), :]
    # Górne dwa punkty
    top_two = sorted_y[:2]
    # Dolne dwa punkty
    bottom_two = sorted_y[2:]

    # Spośród górnych – ten z mniejszym x jest top-left, drugi top-right
    top_two = top_two[np.argsort(top_two[:, 0]), :]
    tl, tr = top_two[0], top_two[1]

    # Spośród dolnych – ten z mniejszym x to bottom-left, drugi bottom-right
    bottom_two = bottom_two[np.argsort(bottom_two[:, 0]), :]
    bl, br = bottom_two[0], bottom_two[1]

    return np.array([tl, tr, bl, br], dtype="float32")


def manual_perspective_with_scaling_and_margin(input_path, output_path='wynik.jpg', display_width=1000, margin=100):
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError("Nie znaleziono obrazu.")

    h, w = img.shape[:2]
    # Obliczenie współczynnika skalowania dla oryginalnego obrazu
    scale = display_width / w if w > display_width else 1.0

    # Przeskaluj oryginalny obraz
    resized_img = cv2.resize(img, (int(w * scale), int(h * scale)))

    # Dodaj margines – tworzymy nowy obraz z białym tłem
    padded_width = resized_img.shape[1] + 2 * margin
    padded_height = resized_img.shape[0] + 2 * margin

    # Białe tło
    display_img = np.ones((padded_height, padded_width, 3), dtype=np.uint8) * 255

    # Wklej oryginalny przeskalowany obraz na środek marginesowanego obrazu
    display_img[margin:margin + resized_img.shape[0], margin:margin + resized_img.shape[1]] = resized_img

    # Ustawienie okna i callbacku
    cv2.namedWindow('Wybierz punkty')
    cv2.setMouseCallback('Wybierz punkty', mouse_callback, param={"scale": scale, "margin": margin})

    print(">>> Kliknij 4 punkty – w dowolnej kolejności.")
    print("Program automatycznie ustali: lewy górny, prawy górny, lewy dolny, prawy dolny.")

    while True:
        temp_img = display_img.copy()
        # Rysuj dotychczas wybrane punkty (przeliczone na skalę wyświetlaną)
        for p in points:
            scaled_p = (int(p[0] * scale + margin), int(p[1] * scale + margin))
            cv2.circle(temp_img, scaled_p, 5, (0, 255, 0), -1)

        cv2.imshow('Wybierz punkty', temp_img)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC – przerwij
            break
        if len(points) >= 4:  # Gdy kliknięto już 4 punkty, wychodzimy z pętli
            break

    cv2.destroyAllWindows()

    if len(points) < 4:
        print("Nie wybrano wystarczającej liczby punktów.")
        return

    # Upewnij się, że używamy tylko 4 punktów (gdyby użytkownik kliknął więcej)
    pts = points[:4]
    # Uporządkuj punkty – automatyczne wykrycie rogów
    pts_src = order_points(pts)

    print("Punkty po uporządkowaniu:")
    print("Top-left:    ", pts_src[0])
    print("Top-right:   ", pts_src[1])
    print("Bottom-left: ", pts_src[2])
    print("Bottom-right:", pts_src[3])

    # Definiujemy docelowy rozmiar wyprostowanego obrazu
    width_target = 1000
    height_target = 500

    pts_dst = np.float32([
        [0, 0],
        [width_target - 1, 0],
        [0, height_target - 1],
        [width_target - 1, height_target - 1]
    ])

    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped = cv2.warpPerspective(img, M, (width_target, height_target))
    cv2.imwrite(output_path, warped)
    print(f"Obraz wyprostowany zapisany jako: {output_path}")


if __name__ == "__main__":
    manual_perspective_with_scaling_and_margin("data/test2.jpg", "data/wynik.jpg", display_width=1000, margin=100)
