import perspectiver as psp
import stave_separator as ss
import box_notes as bn

def handle_array(image, array):
    warped = psp.perspective_with_scaling(image, array)
    staffs = ss.process_image(warped)

    if staffs is None:
        # TODO: print error
        return

    for staff in staffs:
        notes = bn.segment_symbols(staff, margin=5)
        bn.display_notes(notes)

    # TODO: === notes zawiera obiekty klasy music_symbol. Są tam zdjęcia wykrytych symboli w tym nut. ===