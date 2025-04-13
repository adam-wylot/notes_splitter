import perspectiver as psp
import stave_separator as ss
import box_notes as bn

def sheet_image_handler(sheet_image, persp_points_arr):
    warped = psp.perspective_with_scaling(sheet_image, persp_points_arr) # zmiana perspektywy zdjęcia
    staffs, gaps = ss.process_image(warped) # wykrycie pięciolinii

    if staffs is None:
        # TODO: print error
        return

    # Zebranie nut do tablicy [n][k], gdzię: n-ta pięciolinia wkolei (od góry licząc); k-ta nutka
    notes = []
    for staff, gap in zip(staffs, gaps):
        staff_notes = bn.segment_symbols(staff, gap)
        notes.append(staff_notes)
        bn.display_notes(staff_notes) # odkomentować, żeby zobaczyć wycięte nutki

    # [?] === notes zawiera obiekty klasy music_symbol. Są tam zdjęcia wykrytych symboli w tym nut. ===