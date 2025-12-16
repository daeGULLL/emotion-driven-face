def apply_offsets(face_coordinates, offsets):
    x, y, w, h = face_coordinates
    x_off, y_off = offsets
    return (x - x_off, x + w + x_off, y - y_off, y + h + y_off)
