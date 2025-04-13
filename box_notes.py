import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

from music_symbol import MusicSymbol


def is_circular(contour, circularity_thresh_low=0.2, circularity_thresh_high=1.3):
    """
    Sprawdza, czy kontur przypomina okrąg/kółko – wtedy prawdopodobnie jest to nuta.
    Funkcja używa miary kołowości, która jest bezwymiarowa.
    """
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return False
    area = cv2.contourArea(contour)
    circularity = 4 * math.pi * area / (perimeter * perimeter)
    return circularity_thresh_low <= circularity <= circularity_thresh_high


def remove_staff_lines(img, line_thickness=1):
    """
    Usuwa linie pięciolinii z binarnego obrazu 'img'.
    line_thickness określa przybliżoną grubość linii.
    """
    # Budowanie poziomego kernela; długość 50 pikseli – można eksperymentować
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, line_thickness))
    # Erozja usuwa cienkie poziome linie
    eroded = cv2.erode(img, kernel, iterations=2)
    # Odejmujemy wykryte linie od oryginału
    result = cv2.subtract(img, eroded)
    return result


def segment_symbols(staff_image, margin_ratio=0.02, merge_threshold_ratio=0.01, min_area_ratio=0.0001,
                    margin=None, debug=True):
    """
    Funkcja przetwarza obraz pięciolinii (staff_image) i wykrywa na niej symbole muzyczne (np. nuty),
    boxując je na podstawie kształtu. Kryteria takie jak marginesy i progi łączenia przedziałów są
    ustalane dynamicznie na podstawie rozmiaru obrazka.

    Parametry:
      - margin_ratio: stosunek marginesu (w lewo i prawo) do szerokości obrazu (używany, gdy nie podano margin).
      - merge_threshold_ratio: stosunek progu łączenia przedziałów do szerokości obrazu.
      - min_area_ratio: minimalna dopuszczalna powierzchnia konturu (w stosunku do powierzchni obrazu),
                        aby był on traktowany jako potencjalna nuta.
      - margin: opcjonalny margines (w pikselach) – jeśli podany, zastępuje margin_ratio.
      - debug: jeśli True, wyświetla reprezentację diagnostyczną kolejnych etapów przetwarzania obrazu.

    Zwracana jest lista obiektów MusicSymbol posortowanych zgodnie z pozycją x (od lewej).
    """
    # Konwersja obrazu do skali szarości
    gray = cv2.cvtColor(staff_image, cv2.COLOR_BGR2GRAY)
    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(gray, cmap='gray')
        plt.title("Gray Image")
        plt.axis("off")
        plt.show()

    # Binaryzacja z Otsu
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(thresh, cmap='gray')
        plt.title("Threshold (Binarized) Image")
        plt.axis("off")
        plt.show()

    # Usunięcie linii pięciolinii
    thresh_no_lines = remove_staff_lines(thresh, line_thickness=1)
    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(thresh_no_lines, cmap='gray')
        plt.title("After Removing Staff Lines")
        plt.axis("off")
        plt.show()

    # Zamykanie przerw
    closing_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh_closed = cv2.morphologyEx(thresh_no_lines, cv2.MORPH_CLOSE, closing_kernel)
    if debug:
        plt.figure(figsize=(6, 5))
        plt.imshow(thresh_closed, cmap='gray')
        plt.title("After Closing Operation")
        plt.axis("off")
        plt.show()

    # Wykrycie konturów na obrazie pozbawionym linii
    contours, _ = cv2.findContours(thresh_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Rozmiary obrazu – do obliczeń dynamicznych
    img_height, img_width = staff_image.shape[:2]
    image_area = img_height * img_width

    # Ustalenie marginesu; jeśli margin podany, używamy go, w przeciwnym razie margin_ratio
    if margin is None:
        margin = int(margin_ratio * img_width)
    merge_threshold = int(merge_threshold_ratio * img_width)
    min_area = image_area * min_area_ratio

    candidate_intervals = []
    overlay = staff_image.copy()

    # Przetwarzanie konturów – filtracja na podstawie powierzchni i kształtu (kołowości)
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        if not is_circular(cnt):
            continue
        # Rysujemy kontur na obrazie diagnostycznym
        cv2.drawContours(overlay, [cnt], -1, (0, 255, 0), 2)
        x, y, w, h = cv2.boundingRect(cnt)
        # Opcjonalnie rysujemy prostokąt
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 1)
        x_start = max(x - margin, 0)
        x_end = min(x + w + margin, img_width)
        candidate_intervals.append((x_start, x_end))

    if debug:
        plt.figure(figsize=(8, 6))
        plt.imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        plt.title("Detected Candidate Contours")
        plt.axis("off")
        plt.show()

    if not candidate_intervals:
        if debug:
            print("Brak kandydatów na symbole muzyczne.")
        return []

    # Łączenie nakładających się lub bliskich przedziałów – sortujemy po współrzędnej x
    sorted_intervals = sorted(candidate_intervals, key=lambda x: x[0])
    # merged = []
    # for interval in sorted_intervals:
    #     if not merged:
    #         merged.append(interval)
    #     else:
    #         last_start, last_end = merged[-1]
    #         current_start, current_end = interval
    #         if current_start <= last_end + merge_threshold:
    #             new_start = min(last_start, current_start)
    #             new_end = max(last_end, current_end)
    #             merged[-1] = (new_start, new_end)
    #         else:
    #             merged.append(interval)

    # Wizualizacja połączonych przedziałów na oryginalnym obrazie
    overlay2 = staff_image.copy()
    for (x_start, x_end) in sorted_intervals:
        cv2.rectangle(overlay2, (x_start, 0), (x_end, img_height), (0, 0, 255), 2)
    if debug:
        plt.figure(figsize=(8, 6))
        plt.imshow(cv2.cvtColor(overlay2, cv2.COLOR_BGR2RGB))
        plt.title("Merged Note Intervals")
        plt.axis("off")
        plt.show()

    # Wyodrębnienie nut – tworzymy obiekty MusicSymbol dla wykrytych przedziałów
    notes_with_x = []
    for x_start, x_end in sorted_intervals:
        x_end = min(x_end, img_width)
        cropped = staff_image[:, x_start:x_end]
        note_obj = MusicSymbol(cropped)  # Zakładamy, że MusicSymbol przyjmuje obrazek
        notes_with_x.append((x_start, note_obj))

    # Sortowanie nut według pozycji x
    notes_with_x.sort(key=lambda item: item[0])
    sorted_notes = [item[1] for item in notes_with_x]
    return sorted_notes


def display_notes(notes):
    """
    Funkcja do prezentacji wykrytych nut. Dostaje listę obiektów MusicSymbol
    i za pomocą matplotlib pokazuje zdjęcia poszczególnych nut.
    """
    num_notes = len(notes)
    if num_notes == 0:
        print("Brak nut do wyświetlenia.")
        return

    plt.figure(figsize=(num_notes * 3, 4))
    for idx, note in enumerate(notes):
        # Zakładamy, że obiekt MusicSymbol ma atrybut image zawierający obrazek w formacie BGR
        image_rgb = cv2.cvtColor(note.image, cv2.COLOR_BGR2RGB)
        plt.subplot(1, num_notes, idx + 1)
        plt.imshow(image_rgb)
        plt.title(f'Note {idx}')
        plt.axis('off')
    plt.tight_layout()
    plt.show()


# === DEBUG STARTER ===
if __name__ == '__main__':
    staff_image = cv2.imread('output/output_staff_3.png')
    if staff_image is None:
        print("Błąd: Nie udało się wczytać obrazu.")
    else:
        # Ustaw debug=True, aby wyświetlić diagnostykę etapów przetwarzania
        notes = segment_symbols(staff_image, debug=True)
        print(f"Wykryto {len(notes)} nut.")
        display_notes(notes)
