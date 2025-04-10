import cv2
import numpy as np

points = []  # Lista klikniętych punktów (x, y)


def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Dodaj punkt do listy
        points.append((x, y))
        print(f"Kliknięto punkt: {(x, y)}")


def manual_perspective_transform(input_path, output_path='wynik.jpg'):
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError("Nie znaleziono obrazu.")

    # Utwórz okno i przypisz callback
    cv2.namedWindow('Obraz')
    cv2.setMouseCallback('Obraz', mouse_callback)

    print(">>> Kliknij w oknie 4 narożniki w kolejności: top-left, top-right, bottom-left, bottom-right")

    while True:
        # Kopia do podglądu w trakcie klikania
        temp_img = img.copy()
        for p in points:
            cv2.circle(temp_img, p, 5, (0, 255, 0), -1)

        cv2.imshow('Obraz', temp_img)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC - wyjście bez transformacji
            break
        if len(points) == 4:
            # Mamy komplet 4 punktów
            break

    cv2.destroyAllWindows()

    if len(points) < 4:
        print("Nie wybrano 4 punktów. Kończę bez wyjścia.")
        return

    # Przygotuj macierz transformacji
    pts_src = np.float32(points)

    # Tu definiujesz docelowy rozmiar "wyprostowanego" obrazu
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

    # Zapis wyniku
    cv2.imwrite(output_path, warped)
    print(f"Obraz wyprostowany zapisano jako: {output_path}")


if __name__ == "__main__":
    manual_perspective_transform("data/test2.jpg", "data/wynik.jpg")
