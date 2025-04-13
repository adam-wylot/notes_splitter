import os
import sys

import cv2
import numpy as np
import matplotlib.pyplot as plt


def get_image_details(image):
    """
    Konwertuje obraz do skali szarości, binaryzuje oraz wykorzystuje operacje morfologiczne
    z poziomym jądrem, aby wydobyć poziome linie.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Binaryzacja Otsu – linie białe na czarnym tle (odwrócony obraz)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dostosowanie jądra – wybieramy jądro o szerokości zależnej od szerokości obrazu
    kernel_width = max(30, image.shape[1] // 15)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))

    # Operacja morfologiczna typu opening, która usuwa szumy i pozostawia głównie poziome linie
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # Operacja closing – połączenie przerw w wykrytych liniach
    closed_lines = cv2.morphologyEx(detected_lines, cv2.MORPH_CLOSE, horizontal_kernel, iterations=2)

    return binary, closed_lines


def find_lines(detected_lines, image, max_angle=5):
    """
    Wyszukuje kontury w obrazie po operacjach morfologicznych oraz filtruje te,
    które są wystarczająco długie (min_width_ratio * szerokość obrazu), mają mały kąt (max_angle)
    oraz niewielką wysokość (skalowaną w zależności od rozmiaru obrazu).

    Zwraca listę krotek: (x, y, w, h, y_center)
    """
    contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for cnt in contours:
        # Uzyskujemy minimalny prostokąt otaczający
        (cx, cy), (w, h), angle = cv2.minAreaRect(cnt)

        # transformacja kąta
        angle = abs(angle)

        if (angle + 90) % 180 < 45 or 135 < (angle + 90) % 180:
            angle += 90
            w, h = h, w  # zamiana, jeśli potrzebna


        # Kryteria poprawnej linii
        if (h < 1 or w / h > 30) and (angle % 180 < max_angle or angle % 180 > 180 - max_angle) and (h < 30 * (image.shape[0] / 2219)):
            # Obliczenie lewego górnego rogu - przyjmujemy niewielką korektę dla dokładności
            x = int(cx - w / 2)
            y = int(cy - h / 2)
            # Powiększamy prostokąt o zadany współczynnik
            candidates.append((x, y, int(w), int(h), int(cy)))
    candidates.sort(key=lambda item: item[4])

    return candidates


def group_staffs(candidates):
    """
    Grupuje kandydatów (wykryte linie) w pięciolinie muzyczne przy użyciu dynamicznie ustalanych progów,
    dzięki czemu funkcja jest mniej zależna od rozmiaru obrazka.

    Proces działania:
      1. Sortujemy kandydatów według współrzędnej y punktu centralnego (cy).
      2. Obliczamy różnice między kolejnymi wartościami y (centers) i wyznaczamy medianę tych różnic.
         Ta mediana przyjmowana jest jako "typowa" odległość między liniami w obrębie jednej pięciolinii.
      3. Dynamiczny próg oddzielenia pięciolinii (cluster_gap_thresh) ustalamy jako:
             cluster_gap_thresh = median_diff * 1.5
         – dzięki temu większe przerwy między klastrami (czyli między pięcioliniami) są wyłapywane.
      4. Tolerancję grupowania linii w obrębie jednej pięciolinii (group_tolerance) ustalamy jako:
             group_tolerance = median_diff * 0.5
         – mała zmienność odstępów między liniami w obrębie tego samego pięciolinii.
      5. Najpierw kandydaci są dzieleni na klastery, jeśli odstęp między kolejnymi liniami przekracza cluster_gap_thresh.
      6. Następnie w obrębie każdej grupy przeszukiwane są okna pięciu kolejnych linii.
         Jeśli różnica między największą a najmniejszą wartością odstępów (między środkami linii) nie przekracza group_tolerance,
         przyjmujemy to jako poprawnie wyodrębnioną pięciolinię.
    """
    # Sortowanie kandydatów według współrzędnej y środka (cy) – przyjmujemy, że znajduje się on na pozycji indeksu 4
    sorted_candidates = sorted(candidates, key=lambda c: c[4])

    # Jeśli mamy mniej niż dwa elementy, nie da się obliczyć odstępu
    if len(sorted_candidates) < 2:
        return []

    # Wyciągamy wszystkie środki linii i obliczamy różnice między kolejnymi
    centers = [c[4] for c in sorted_candidates]
    diffs = np.diff(centers)
    median_diff = np.median(diffs)

    # Dynamicznie ustalane progi (można zmieniać mnożniki w zależności od specyfiki obrazka)
    cluster_gap_thresh = median_diff * 1.5
    group_tolerance = median_diff * 0.5

    # Etap 1: Klasteryzacja – grupowanie kandydatów, gdy różnica między środkami jest mniejsza niż cluster_gap_thresh
    clusters = []
    current_cluster = []
    for cand in sorted_candidates:
        if not current_cluster:
            current_cluster.append(cand)
        else:
            prev_center = current_cluster[-1][4]
            if cand[4] - prev_center < cluster_gap_thresh:
                current_cluster.append(cand)
            else:
                clusters.append(current_cluster)
                current_cluster = [cand]
    if current_cluster:
        clusters.append(current_cluster)

    # Etap 2: W obrębie każdego klastra szukamy okien 5 kolejnych linii spełniających warunek spójności
    groups = []
    for cluster in clusters:
        if len(cluster) < 5:
            continue
        n = len(cluster)
        for i in range(n - 4):
            group = cluster[i:i + 5]
            group_centers = [item[4] for item in group]
            group_diffs = np.diff(group_centers)
            # Jeżeli różnica między największym a najmniejszym odstępem w grupie mieści się w dynamicznej tolerancji,
            # uznajemy grupę za spójną pięciolinię
            if np.max(group_diffs) - np.min(group_diffs) <= group_tolerance:
                groups.append(group)

    # Opcjonalnie: wybieramy unikalne pięciolinie, aby uniknąć nakładających się detekcji
    final_groups = []
    used = set()
    for group in groups:
        key = group[0][4]
        if key not in used:
            final_groups.append(group)
            for item in group:
                used.add(item[4])
    return final_groups


def extract_staffs(image, groups):
    """
    Dla każdej grupy (pięciolini) określa pionowy obszar obejmujący staff (z dolanym marginesem)
    i wycina go z całego obrazu.
    """
    regions = []
    gaps = []
    for group in groups:
        diff = abs(group[0][4] - group[1][4])
        gaps.append(diff)

        top = int(min(item[1] for item in group)) - 3*diff
        bottom = int(max(item[1] + item[3] for item in group)) + 3*diff

        top = max(top, 0)
        bottom = min(bottom, image.shape[0])

        region = image[top:bottom, :]
        regions.append(region)
    return regions, gaps


def process_image(image, debug=False):
    # 1. Detekcja linii i zwrócenie obrazów pośrednich
    binary, detected_lines_cont = get_image_details(image)

    # Wizualizacja etapów przetwarzania
    if debug:
        plt.figure(figsize=(15, 8))
        plt.subplot(231), plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), plt.title('Oryginał')
        plt.subplot(232), plt.imshow(binary, cmap='gray'), plt.title('Binaryzacja Otsu (odwrócona)')
        plt.subplot(233), plt.imshow(detected_lines_cont, cmap='gray'), plt.title('Po operacjach morfologicznych')

    # 2. Znalezienie kandydatów
    candidates = find_lines(detected_lines_cont, image)
    img_candidates = image.copy()
    for cand in candidates:
        x, y, w, h, _ = cand
        cv2.rectangle(img_candidates, (x, y), (x + w, y + h), (0, 255, 0), 2)
    if debug:
        plt.subplot(234), plt.imshow(cv2.cvtColor(img_candidates, cv2.COLOR_BGR2RGB)), plt.title(f'Kandydaci: {len(candidates)}')

    if not candidates:
        print("Nie wykryto żadnych poziomych linii")
        return


    # 3. Grupowanie kandydatów w staffy (pięciolinie)
    groups = group_staffs(candidates)
    img_groups = image.copy()
    colors = plt.get_cmap('hsv', len(groups)+1)  # <--- TU BYŁ PROBLEM
    for i, group in enumerate(groups):
        color = [int(255*c) for c in colors(i)[:3]]
        for cand in group:
            x, y, w, h, _ = cand
            cv2.rectangle(img_groups, (x,y), (x+w,y+h), color, 3)
    if debug:
        plt.subplot(235), plt.imshow(cv2.cvtColor(img_groups, cv2.COLOR_BGR2RGB)), plt.title(f'Pogrupowane: {len(groups)}')
        plt.tight_layout()
        plt.show()

    if not groups:
        print("Nie znaleziono kompletnych pięciolinii")
        return


    # 4. Wycięcie regionów staffów
    staffs, gaps = extract_staffs(image, groups)

    # # Utwórz folder output, jeśli nie istnieje
    # os.makedirs('output', exist_ok=True)
    #
    # for i, region in enumerate(staff_regions, 1):
    #     output_name = os.path.join('output', f"output_staff_{i}.png")  # Zmieniona ścieżka
    #     cv2.imwrite(output_name, region)
    #     print(f"Zapisano wykrytą pięciolinię nr {i} do pliku {output_name}")

    # 5. Wizualizacja wyników przy pomocy matplotlib (jeżeli tryb debug)
    if debug:
        cols = 2
        rows = (len(staffs) + cols - 1) // cols
        plt.figure(figsize=(12, 5 * rows))
        for i, region in enumerate(staffs, 1):
            plt.subplot(rows, cols, i)
            plt.imshow(cv2.cvtColor(region, cv2.COLOR_BGR2RGB))
            plt.title(f"Pięciolinia {i}")
            plt.axis("off")
        plt.tight_layout()
        plt.show()

    return staffs, gaps


if __name__ == '__main__':
    image_path = "data/wlazl_kotek_na_plotek.jpg"  # Podmień na ścieżkę do obrazu z nutami
    image = cv2.imread(image_path)
    if image is None:
        sys.exit(1)

    process_image(image, True)
