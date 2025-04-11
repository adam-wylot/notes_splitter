import cv2
import numpy as np
import math
import matplotlib.pyplot as plt


class Note:
    def __init__(self, image):
        self.image = image


def is_circular(contour, circularity_thresh_low=0.4, circularity_thresh_high=1.1):
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return False
    area = cv2.contourArea(contour)
    circularity = 4 * math.pi * area / (perimeter * perimeter)
    return circularity >= circularity_thresh_low and circularity <= circularity_thresh_high


def segment_open_notes_from_staff(staff_image, margin=5, merge_threshold=5):
    gray = cv2.cvtColor(staff_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidate_intervals = []
    img_height, img_width = staff_image.shape[:2]

    for cnt in contours:
        if cv2.contourArea(cnt) < 10:
            continue
        if not is_circular(cnt):
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        x_start = max(x - margin, 0)
        x_end = min(x + w + margin, img_width)
        candidate_intervals.append((x_start, x_end))

    if not candidate_intervals:
        return []

    # Łączenie nakładających się lub bliskich przedziałów
    sorted_intervals = sorted(candidate_intervals, key=lambda x: x[0])
    merged = []
    for interval in sorted_intervals:
        if not merged:
            merged.append(interval)
        else:
            last_start, last_end = merged[-1]
            current_start, current_end = interval
            if current_start <= last_end + merge_threshold:
                new_start = min(last_start, current_start)
                new_end = max(last_end, current_end)
                merged[-1] = (new_start, new_end)
            else:
                merged.append(interval)

    notes_with_x = []
    for x_start, x_end in merged:
        x_end = min(x_end, img_width)
        cropped = staff_image[0:img_height, x_start:x_end]
        note_obj = Note(cropped)
        notes_with_x.append((x_start, note_obj))

    notes_with_x.sort(key=lambda item: item[0])
    sorted_notes = [item[1] for item in notes_with_x]
    return sorted_notes


def display_notes(notes):
    num_notes = len(notes)
    if num_notes == 0:
        print("Brak nut do wyświetlenia.")
        return

    plt.figure(figsize=(num_notes * 3, 4))
    for idx, note in enumerate(notes):
        image_rgb = cv2.cvtColor(note.image, cv2.COLOR_BGR2RGB)
        plt.subplot(1, num_notes, idx + 1)
        plt.imshow(image_rgb)
        plt.title(f'Note {idx}')
        plt.axis('off')
    plt.tight_layout()
    plt.show()


# Przykład użycia pozostaje bez zmian
staff_image = cv2.imread('output/output_staff_3.png')
if staff_image is None:
    print("Błąd: Nie udało się wczytać obrazu.")
else:
    notes = segment_open_notes_from_staff(staff_image, margin=5)
    print(f"Wykryto {len(notes)} nut.")
    display_notes(notes)