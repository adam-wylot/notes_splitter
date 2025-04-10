import os

import cv2
import numpy as np
import matplotlib.pyplot as plt


def detect_staff_lines(image):
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
    return binary, detected_lines


def find_line_candidates(detected_lines, image, min_width_ratio=0.3, max_line_height=15):
    """
    Wyszukuje kontury w obrazie po operacjach morfologicznych oraz filtruje te,
    które są wystarczająco długie (min_width_ratio * szerokość obrazu) i mają małą wysokość.

    Zwraca listę krotek: (x, y, w, h, y_center)
    """
    contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > image.shape[1] * min_width_ratio and h < max_line_height:
            y_center = y + h / 2.0
            candidates.append((x, y, w, h, y_center))
    # Sortowanie według środkowej pozycji Y
    candidates.sort(key=lambda item: item[4])
    return candidates


def group_staffs(candidates, cluster_gap_thresh=40, group_tolerance=30):
    """
    Grupuje kandydatów (wykryte linie) w dwa etapy:
      1. Klasteryzacja – kandydaci są dzieleni na klastry, jeśli odstęp między ich środkami
         przekracza cluster_gap_thresh.
      2. W każdym klastrze sprawdzane są przesuwane okna 5 kolejnych linii; jeżeli różnica
         między maksymalnym a minimalnym odstępem między liniami w oknie nie przekracza group_tolerance,
         uznajemy to za wykrytą pięciolinię.
    """
    clusters = []
    current_cluster = []
    # Klasteryzacja kandydatów – korzystamy z sortowania według y_center
    for i, cand in enumerate(candidates):
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

    groups = []
    # Dla każdego klastra – jeśli ma przynajmniej 5 kandydatów, wyciągamy grupy
    for cluster in clusters:
        if len(cluster) < 5:
            continue
        n = len(cluster)
        for i in range(n - 4):
            group = cluster[i:i + 5]
            centers = [item[4] for item in group]
            diffs = np.diff(centers)
            # Jeżeli różnica między największym a najmniejszym odstępem pomiędzy liniami jest mniejsza niż tolerance,
            # uznajemy grupę za spójną pięciolinię.
            if np.max(diffs) - np.min(diffs) <= group_tolerance:
                groups.append(group)
    # Jeśli powstało wiele nakładających się grup, wybieramy te unikalne (np. na podstawie środka pierwszej linii)
    final_groups = []
    used = set()
    for group in groups:
        key = group[0][4]
        if key not in used:
            final_groups.append(group)
            for item in group:
                used.add(item[4])
    return final_groups


def extract_staff_regions(image, groups, margin=10):
    """
    Dla każdej grupy (pięciolini) określa pionowy obszar obejmujący staff (z dolanym marginesem)
    i wycina go z całego obrazu.
    """
    regions = []
    for group in groups:
        top = int(min(item[1] for item in group)) - margin
        bottom = int(max(item[1] + item[3] for item in group)) + margin

        top = max(top, 0)
        bottom = min(bottom, image.shape[0])

        region = image[top:bottom, :]
        regions.append(region)
    return regions


def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Błąd wczytania obrazu")
        return

    # 1. Detekcja linii i zwrócenie obrazów pośrednich
    binary, detected_lines = detect_staff_lines(image)  # Nowy unpacking

    # Wizualizacja etapów przetwarzania
    plt.figure(figsize=(15, 8))
    plt.subplot(231), plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), plt.title('Oryginał')
    plt.subplot(232), plt.imshow(binary, cmap='gray'), plt.title('Binaryzacja Otsu (odwrócona)')
    plt.subplot(233), plt.imshow(detected_lines, cmap='gray'), plt.title('Po operacjach morfologicznych')

    # 2. Znalezienie kandydatów
    candidates = find_line_candidates(detected_lines, image, min_width_ratio=0.3, max_line_height=15)
    img_candidates = image.copy()
    for cand in candidates:
        x, y, w, h, _ = cand
        cv2.rectangle(img_candidates, (x, y), (x + w, y + h), (0, 255, 0), 2)
    plt.subplot(234), plt.imshow(cv2.cvtColor(img_candidates, cv2.COLOR_BGR2RGB)), plt.title(
        f'Kandydaci: {len(candidates)}')

    if not candidates:
        print("Nie wykryto żadnych poziomych linii")
        return


    # 3. Grupowanie kandydatów w staffy (pięciolinie)
    groups = group_staffs(candidates, cluster_gap_thresh=20, group_tolerance=10)
    img_groups = image.copy()
    # Zmiana: użyj plt.get_cmap() zamiast plt.cm.get_cmap()
    colors = plt.get_cmap('hsv', len(groups)+1)  # <--- TU BYŁ PROBLEM
    for i, group in enumerate(groups):
        color = [int(255*c) for c in colors(i)[:3]]
        for cand in group:
            x, y, w, h, _ = cand
            cv2.rectangle(img_groups, (x,y), (x+w,y+h), color, 3)
    plt.subplot(235), plt.imshow(cv2.cvtColor(img_groups, cv2.COLOR_BGR2RGB)), plt.title(f'Pogrupowane: {len(groups)}')
    plt.tight_layout()
    plt.show()

    if not groups:
        print("Nie znaleziono kompletnych pięciolinii")
        return


    # 4. Wycięcie regionów staffów
    staff_regions = extract_staff_regions(image, groups, margin=10)

    # Utwórz folder output, jeśli nie istnieje
    os.makedirs('output', exist_ok=True)

    for i, region in enumerate(staff_regions, 1):
        output_name = os.path.join('output', f"output_staff_{i}.png")  # Zmieniona ścieżka
        cv2.imwrite(output_name, region)
        print(f"Zapisano wykrytą pięciolinię nr {i} do pliku {output_name}")

    # 5. Wizualizacja wyników przy pomocy matplotlib
    cols = 2
    rows = (len(staff_regions) + cols - 1) // cols
    plt.figure(figsize=(12, 5 * rows))
    for i, region in enumerate(staff_regions, 1):
        plt.subplot(rows, cols, i)
        plt.imshow(cv2.cvtColor(region, cv2.COLOR_BGR2RGB))
        plt.title(f"Pięciolinia {i}")
        plt.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    image_path = "data/wynik.jpg"  # Podmień na ścieżkę do obrazu z nutami
    process_image(image_path)
