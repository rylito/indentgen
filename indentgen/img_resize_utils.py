from PIL import Image

def resize(abs_path_in, abs_path_out, max_width, max_height):
    with Image.open(abs_path_in) as im:
        if im.width > max_width or im.height > max_height:
            im.thumbnail((max_width, max_height))

        abs_path_out.parent.mkdir(parents=True, exist_ok=True)
        im.save(abs_path_out, "PNG")


