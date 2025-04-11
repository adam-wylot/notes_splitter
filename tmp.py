import cv2 as cv
import numpy as np
import os

def split_staves(image, output_dir="output", threshold_ratio=0.4, line_gap=10):
    # Tworzenie folderu wyjściowego
    # os.makedirs(output_dir, exist_ok=True)

    # Konwersja do jednego kanału koloru — odcieni szarości
    gray_img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    # Binarna wersja obrazu (linie na czarno)
    _, binary = cv.threshold(gray_img, 200, 255, cv.THRESH_BINARY_INV)

    # Sumowanie czarnych pikseli w poziomie
    horizontal_sum = np.sum(binary, axis=1)

    # Ustalenie progu, powyżej którego uznajemy wiersz za część pięciolinii
    threshold = np.max(horizontal_sum) * threshold_ratio
    staff_lines = np.where(horizontal_sum > threshold)[0]

    # Grupowanie linii w systemy pięciolinii
    systems = []
    current_system = []

    for i in range(len(staff_lines) - 1):
        current_system.append(staff_lines[i])
        if staff_lines[i+1] - staff_lines[i] > line_gap:
            if len(current_system) >= 5:
                systems.append(current_system)
            current_system = []

    if len(current_system) >= 5:
        systems.append(current_system)

    # Wycinanie i zapisywanie każdej pięciolinii
    output_paths = []
    for idx, system in enumerate(systems):
        top = max(0, system[0] - 40)
        bottom = min(image.shape[0], system[-1] + 40)
        system_img = image[top:bottom, :]
        output_path = os.path.join(output_dir, f"{idx+1}.png")
        cv.imwrite(output_path, system_img)
        output_paths.append(output_path)

    return output_paths