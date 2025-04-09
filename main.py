import stave_separator as sp

import cv2 as cv
import sys

# MAIN
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # Wczytanie obrazka ze ścieżki argumentu
        input_path = sys.argv[1] # C:/Users/adamw/Desktop/kotek.png
        image = cv.imread(input_path)

        # Tworzenie kontenera pięcioliniami
        results = sp.split_staves(image) # [n][2]

        # print("Wykryto i zapisano pięciolinie:")
        # for path in results:
        #     print(path)
    else:
        print("Nie podano ścieżki do pliku!")