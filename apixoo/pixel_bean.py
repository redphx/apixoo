from PIL import Image


class PixelBean(object):
    @property
    def total_frames(self):
        return self._total_frames

    @property
    def speed(self):
        return self._speed

    @property
    def row_count(self):
        return self._row_count

    @property
    def column_count(self):
        return self._column_count

    @property
    def palettes(self):
        return self._palettes

    @property
    def frames_data(self):
        return self._frames_data

    def __init__(
        self,
        total_frames: int,
        speed: int,
        row_count: int,
        column_count: int,
        palettes: list,
        frames_data: list,
    ):
        self._total_frames = total_frames
        self._speed = speed
        self._row_count = row_count
        self._column_count = column_count
        self._palettes = palettes
        self._frames_data = frames_data

    def save_to_gif(self, output_path: str, scale: int = 1) -> None:
        gif_frames = []

        idx = 0
        for current_frame, frame_data in enumerate(self._frames_data):
            img = Image.new('RGBA', (self._column_count * 16, self._row_count * 16))
            for y in range(self._row_count * 16):
                for x in range(self.column_count * 16):
                    palette_index = frame_data[y][x]
                    rgb = self._palettes[palette_index]
                    img.putpixel((x, y), rgb)

            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
            idx += 1
            gif_frames.append(img)

        gif_frames[0].save(
            output_path,
            append_images=gif_frames[1:],
            duration=(1000 / self._speed),
            save_all=True,
            optimize=False,
            interlace=False,
            loop=0,
            disposal=0,
        )
