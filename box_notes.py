import cv2
import numpy as np
import math
import matplotlib.pyplot as plt



def is_circular(cnt, circularity_thresh_low=0.6, circularity_thresh_high=1.3):
    """
    Funkcja oblicza miarę kołowości konturu:
       circularity = 4*pi * (area) / (perimeter^2)
    Dla idealnego koła wartość ta wynosi 1.0.
    Ustawiając dolny próg na 0.1, akceptujemy również kontury z wewnętrznymi otworami.
    """
    (_, _), (w, h), _ = cv2.minAreaRect(cnt)
    aspect_ratio = w / h if h != 0 else 0

    if 1.3 < aspect_ratio or aspect_ratio < 0.5:
        return False


    perimeter = cv2.arcLength(cnt, True)
    if perimeter == 0:
        return False
    area = cv2.contourArea(cnt)
    circularity = 4 * math.pi * area / (perimeter ** 2)
    return circularity_thresh_low <= circularity <= circularity_thresh_high


def remove_lines(binary_image, line_length_ratio=0.5, debug=False):
    """
    Usuwa poziome linie (np. pięciolinię) z binarnego obrazu.
    Przy pomocy otwarcia morfologicznego z poziomym kernelem.
    """
    h, w = binary_image.shape

    hor_kernel_length = int(w * line_length_ratio)
    ver_kernel_length = int(h * line_length_ratio)

    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hor_kernel_length, 1))
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_kernel_length))

    temp1 = cv2.erode(binary_image, hor_kernel, iterations=1)
    temp2 = cv2.erode(binary_image, ver_kernel, iterations=1)

    detected_hor_lines = cv2.dilate(temp1, hor_kernel, iterations=1)
    detected_ver_lines = cv2.dilate(temp2, ver_kernel, iterations=1)

    result = cv2.subtract(binary_image, detected_hor_lines)
    result = cv2.subtract(result, detected_ver_lines)

    if debug:
        plt.figure(figsize=(10, 4))
        plt.subplot(1, 4, 1)
        plt.imshow(binary_image, cmap='gray')
        plt.title("Binary Input")
        plt.axis('off')

        plt.subplot(1, 4, 2)
        plt.imshow(detected_hor_lines, cmap='gray')
        plt.title("Detected Horizontal Lines")
        plt.axis('off')

        plt.subplot(1, 4, 3)
        plt.imshow(detected_ver_lines, cmap='gray')
        plt.title("Detected Vertical Lines")
        plt.axis('off')

        plt.subplot(1, 4, 4)
        plt.imshow(result, cmap='gray')
        plt.title("After Line Removal")
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    return result


def detect_symbols(image, gap, debug=False):
    """
    Pipeline do wykrywania wyłącznie okrągłych obiektów.

    Kroki:
      1. Wczytanie obrazu, konwersja do skali szarości i binaryzacja.
      2. Odwrócenie binaryzowanego obrazu (nuty będą białe, tło czarne).
      3. Usunięcie poziomych linii (np. pięciolinia) – opcjonalnie, jeśli nie chcemy wykrywać tych linii.
      4. Opcjonalne operacje morfologiczne (closing/opening), aby „uporządkować” kształty.
      5. Wykrywanie konturów.
      6. Filtracja konturów przy pomocy funkcji is_circular.
      7. Boxowanie wykrytych obiektów.
    """
    # Wczytanie obrazu
    bgr = image
    if bgr is None:
        print("Błąd wczytania obrazu.")
        return []

    # Konwersja do skali szarości
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Binaryzacja – korzystamy z metody Otsu i odwracamy obraz,
    # żeby obiekty miały wartość 255 (białe), a tło 0 (czarne)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_inv = cv2.bitwise_not(binary)

    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(binary_inv, cmap='gray')
        plt.title("Binary Inverted")
        plt.axis('off')
        plt.show()

    # Usuwanie poziomych linii – można wyłączyć, jeśli nie chcemy usuwać pięciolinii
    lines_removed = remove_lines(binary_inv, line_length_ratio=0.3, debug=debug)

    # Opcjonalne operacje morfologiczne
    # Closing z kernelem 5x5, aby zamknąć ewentualne otwory w okrągłych obiektach
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(lines_removed, cv2.MORPH_CLOSE, kernel_close)

    # Opening 3x3, aby usunąć drobne szumy
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    processed = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(processed, cmap='gray')
        plt.title("After Morphology")
        plt.axis('off')
        plt.show()

    # Znalezienie konturów – wybieramy RETR_EXTERNAL, by brać tylko zewnętrzne kształty
    contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    overlay = bgr.copy()
    boxes = []
    h, w = processed.shape
    image_area = h * w

    # Minimalna powierzchnia, żeby pominąć bardzo małe artefakty (możesz dostosować)
    min_area = 0.0003 * image_area

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        # Sprawdzamy czy kontur jest wystarczająco „okrągły”
        if not is_circular(cnt, circularity_thresh_low=0.4, circularity_thresh_high=1.2):
            continue

        # Wyznaczamy bounding box dla konturu
        x, _, bw, _ = cv2.boundingRect(cnt)
        margin = int(0.3 * gap)
        x_start = max(x - margin, 0)
        y_start = 0
        x_end = min(x + bw + margin, w)
        y_end = h
        boxes.append((x_start, y_start, x_end - x_start, y_end - y_start))
        cv2.rectangle(overlay, (x_start, y_start), (x_end, y_end), (0, 0, 255), 2)

    if debug:
        plt.figure(figsize=(12, 6))
        plt.imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        plt.title("Detected Circular Objects (Red Boxes)")
        plt.axis('off')
        plt.show()

    return boxes


if __name__ == "__main__":
    # Podmień na ścieżkę do Twojego obrazu
    img_path = "wlazl_kotek_na_plotek.jpg"
    boxes = detect_symbols(img_path, 5, debug=True)
    print(f"Wykryto {len(boxes)} potencjalnych okrągłych obiektów.")
