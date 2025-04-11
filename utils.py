import perspectiver as psp
import stave_separator as ss

def handle_array(image, array):
    print("Odebrano tablicę z MainWindow:")
    print(array)

    warped = psp.perspective_with_scaling(image, array)
    ss.process_image(warped)