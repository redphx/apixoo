from typing import Union

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

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

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

        self._width = column_count * 16
        self._height = row_count * 16

    def _resize(
        self,
        img: Image,
        scale: Union[int, float] = 1,
        target_width: int = None,
        target_height: int = None,
    ) -> Image:
        """Resize frame image"""
        # Default params -> don't do anything
        if scale == 1 and not target_width and not target_height:
            return img

        org_width = img.width
        org_height = img.height

        width = img.width
        height = img.height

        if scale != 1:
            width = round(width * scale)
            height = round(height * scale)
        elif target_width or target_height:
            # Set specific width/height
            if target_width and target_height:
                width = target_width
                height = target_height
            elif target_width and not target_height:
                width = target_width
                height = round((target_width * org_height) / org_width)
            elif target_height and not target_width:
                width = round((target_height * org_width) / org_height)
                height = target_height

        # Resize image if needed
        if width != org_width or height != org_height:
            img = img.resize((width, height), Image.NEAREST)

        return img

    def get_frame_image(
        self,
        frame_number: int,
        scale: Union[int, float] = 1,
        target_width: int = None,
        target_height: int = None,
    ) -> Image:
        """Get Pillow Image of a frame"""
        if frame_number <= 0 or frame_number > self.total_frames:
            raise Exception('Frame number out of range!')

        frame_data = self._frames_data[frame_number - 1]
        img = Image.new('RGB', (self._width, self._height))
        for y in range(self._row_count * 16):
            for x in range(self.column_count * 16):
                palette_index = frame_data[y][x]
                rgb = self._palettes[palette_index]
                img.putpixel((x, y), rgb)

        img = self._resize(
            img, scale=scale, target_width=target_width, target_height=target_height
        )
        return img

    def save_to_gif(
        self,
        output_path: str,
        scale: Union[int, float] = 1,
        target_width: int = None,
        target_height: int = None,
    ) -> None:
        """Convert animation to GIF file"""
        gif_frames = []

        for frame_number in range(self._total_frames):
            img = self.get_frame_image(
                frame_number + 1,
                scale=scale,
                target_width=target_width,
                target_height=target_height,
            )
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
