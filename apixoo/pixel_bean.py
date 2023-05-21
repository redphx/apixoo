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

    def save_to_gif(
        self,
        output_path: str,
        scale: int | float = 1,
        width: int = None,
        height: int = None,
    ) -> None:
        """Convert animation to GIF file"""
        gif_frames = []

        org_width = self._column_count * 16
        org_height = self._row_count * 16

        for _, frame_data in enumerate(self._frames_data):
            img = Image.new('RGBA', (org_width, org_height))
            for y in range(self._row_count * 16):
                for x in range(self.column_count * 16):
                    palette_index = frame_data[y][x]
                    rgb = self._palettes[palette_index]
                    img.putpixel((x, y), rgb)

            # Scale image
            if scale != 1:
                width = round(img.width * scale)
                height = round(img.height * scale)
            else:
                # Set specific width/height
                if width and not height:
                    height = round((width * org_height) / org_width)
                elif height and not width:
                    width = round((height * org_width) / org_height)

            # Resize image if needed
            if width != org_width and height != org_height:
                img = img.resize((width, height), Image.NEAREST)

            gif_frames.append(img)

        # Save to GIF
        gif_frames[0].save(
            output_path,
            append_images=gif_frames[1:],
            duration=self._speed,
            save_all=True,
            optimize=False,
            interlace=False,
            loop=0,
            disposal=0,
        )
