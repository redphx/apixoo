import json
from enum import Enum
from io import IOBase
from struct import unpack

import lzo
from Crypto.Cipher import AES

from .pixel_bean import PixelBean


class FileFormat(Enum):
    PIC_MULTIPLE = 17

    ANIM_SINGLE = 9  # 16x16
    ANIM_MULTIPLE = 18  # 32x32 or 64x64
    ANIM_MULTIPLE_64 = 26  # 64x64, new format


class BaseDecoder(object):
    AES_SECRET_KEY = '78hrey23y28ogs89'
    AES_IV = '1234567890123456'.encode('utf8')

    def __init__(self, fp: IOBase):
        self._fp = fp

    def decode() -> PixelBean:
        raise Exception('Not implemented!')

    def _decrypt_aes(self, data):
        cipher = AES.new(
            self.AES_SECRET_KEY.encode('utf8'),
            AES.MODE_CBC,
            self.AES_IV,
        )
        return cipher.decrypt(data)

    def _compact(self, frames_data, total_frames, row_count=1, column_count=1):
        frame_size = row_count * column_count * 16 * 16 * 3

        palettes = []
        frames_compact = json.loads(
            json.dumps(
                [[[None] * (column_count * 16)] * (row_count * 16)] * total_frames
            )
        )

        for current_frame, frame_data in enumerate(frames_data):
            pos = 0
            x = 0
            y = 0
            grid_x = 0
            grid_y = 0

            while pos < frame_size:
                r, g, b = unpack('BBB', frame_data[pos : pos + 3])
                rgb = (r, g, b)

                try:
                    palette_index = palettes.index(rgb)
                except ValueError:
                    palettes.append(rgb)
                    palette_index = len(palettes) - 1

                real_x = x + (grid_x * 16)
                real_y = y + (grid_y * 16)

                frames_compact[current_frame][real_y][real_x] = palette_index

                x += 1
                pos += 3
                if (pos / 3) % 16 == 0:
                    x = 0
                    y += 1

                if (pos / 3) % 256 == 0:
                    x = 0
                    y = 0
                    grid_x += 1

                    if grid_x == row_count:
                        grid_x = 0
                        grid_y += 1

        return (palettes, frames_compact)


class AnimSingleDecoder(BaseDecoder):
    def decode(self) -> PixelBean:
        content = b'\x00' + self._fp.read()  # Add back the first byte (file type)

        # Re-arrange data
        encrypted_data = bytearray(len(content) - 4)
        for i in range(len(content)):
            encrypted_data[i - 4] = content[i]

        row_count = 1
        column_count = 1
        speed = unpack('>H', content[2:4])[0]

        # Decrypt AES
        decrypted_data = self._decrypt_aes(encrypted_data)
        total_frames = len(decrypted_data) // 768

        # Parse frames data
        frames_data = []
        for i in range(total_frames):
            pos = i * 768
            frames_data.append(decrypted_data[pos : pos + 768])

        # Compact data
        palettes, frames_compact = self._compact(frames_data, total_frames)

        return PixelBean(
            total_frames,
            speed,
            row_count,
            column_count,
            palettes,
            frames_compact,
        )


class AnimMultiDecoder(BaseDecoder):
    def decode(self) -> PixelBean:
        total_frames, speed, row_count, column_count = unpack('>BHBB', self._fp.read(5))
        encrypted_data = self._fp.read()

        return self._decode_frames_data(
            encrypted_data, total_frames, speed, row_count, column_count
        )

    def _decode_frames_data(
        self, encrypted_data, total_frames, speed, row_count, column_count
    ):
        width = 16 * column_count
        height = 16 * row_count

        data = self._decrypt_aes(encrypted_data)
        uncompressed_frame_size = width * height * 3
        pos = 0

        frames_data = [] * total_frames
        for current_frame in range(total_frames):
            frame_size = unpack('>I', data[pos : pos + 4])[0]
            pos += 4

            frame_data = lzo.decompress(
                data[pos : pos + frame_size], False, uncompressed_frame_size
            )
            pos += frame_size

            frames_data.append(frame_data)

        palettes, frames_compact = self._compact(
            frames_data, total_frames, row_count, column_count
        )

        return PixelBean(
            total_frames,
            speed,
            row_count,
            column_count,
            palettes,
            frames_compact,
        )


class AnimMulti64Decoder(BaseDecoder):
    def _get_dot_info(self, data, pos, pixel_idx, bVar9):
        if not data[pos:]:
            return -1

        uVar2 = bVar9 * pixel_idx & 7
        uVar4 = bVar9 * pixel_idx * 65536 >> 0x13

        if bVar9 < 9:
            uVar3 = bVar9 + uVar2
            if uVar3 < 9:
                uVar6 = data[pos + uVar4] << (8 - uVar3 & 0xFF) & 0xFF
                uVar6 >>= uVar2 + (8 - uVar3) & 0xFF
            else:
                uVar6 = data[pos + uVar4 + 1] << (0x10 - uVar3 & 0xFF) & 0xFF
                uVar6 >>= 0x10 - uVar3 & 0xFF
                uVar6 &= 0xFFFF
                uVar6 <<= 8 - uVar2 & 0xFF
                uVar6 |= data[pos + uVar4] >> uVar2
        else:
            raise Exception('(2) Unimplemented')

        return uVar6

    def _decode_frame_data(self, data):
        output = [None] * 12288
        encrypt_type = data[5]
        if encrypt_type != 0x0C:
            raise Exception('Unsupported %s' % encrypt_type)

        uVar13 = data[6]
        iVar11 = uVar13 * 3

        if uVar13 == 0:
            bVar9 = 8
            iVar11 = 768  # Fix corrupted frame
        else:
            bVar9 = 0xFF
            bVar15 = 1
            while True:
                if (uVar13 & 1) != 0:
                    bVar18 = bVar9 == 0xFF
                    bVar9 = bVar15
                    if bVar18:
                        bVar9 = bVar15 - 1

                uVar14 = uVar13 & 0xFFFE
                bVar15 = bVar15 + 1
                uVar13 = uVar14 >> 1
                if uVar14 == 0:
                    break

        pixel_idx = 0
        pos = (iVar11 + 8) & 0xFFFF

        while True:
            color_index = self._get_dot_info(data, pos, pixel_idx & 0xFFFF, bVar9)

            target_pos = pixel_idx * 3
            if color_index == -1:  # transparent -> black
                output[target_pos] = 0
                output[target_pos + 1] = 0
                output[target_pos + 2] = 0
            else:
                color_pos = 8 + color_index * 3

                output[target_pos] = data[color_pos]
                output[target_pos + 1] = data[color_pos + 1]
                output[target_pos + 2] = data[color_pos + 2]

            pixel_idx += 1
            if pixel_idx == 4096:  # 64x64
                break

        return bytearray(output)

    def decode(self) -> PixelBean:
        total_frames, speed, row_count, column_count = unpack('>BHBB', self._fp.read(5))
        frames_data = [] * total_frames

        for frame in range(total_frames):
            size = unpack('>I', self._fp.read(4))[0]
            frame_data = self._decode_frame_data(self._fp.read(size))

            frames_data.append(frame_data)

        palettes, frames_compact = self._compact(
            frames_data, total_frames, row_count, column_count
        )

        return PixelBean(
            total_frames,
            speed,
            row_count,
            column_count,
            palettes,
            frames_compact,
        )
        pass


class PicMultiDecoder(BaseDecoder):
    def decode(self) -> PixelBean:
        row_count, column_count, length = unpack('>BBI', self._fp.read(6))
        encrypted_data = self._fp.read()

        width = 16 * column_count
        height = 16 * row_count
        uncompressed_frame_size = width * height * 3

        data = self._decrypt_aes(encrypted_data)

        frame_data = lzo.decompress(data[:length], False, uncompressed_frame_size)
        frames_data = [frame_data]
        total_frames = 1
        speed = 40
        palettes, frames_compact = self._compact(
            frames_data, total_frames, row_count, column_count
        )

        # TODO: support showing string when remaning length > 20
        return PixelBean(
            total_frames,
            speed,
            row_count,
            column_count,
            palettes,
            frames_compact,
        )


class PixelBeanDecoder(object):
    def decode_file(file_path: str) -> PixelBean:
        with open(file_path, 'rb') as fp:
            return PixelBeanDecoder.decode_stream(fp)

    def decode_stream(fp: IOBase) -> PixelBean:
        try:
            file_format = unpack('B', fp.read(1))[0]
            file_format = FileFormat(file_format)
        except Exception:
            print(f'Unsupported file format: {file_format}')
            return None

        if file_format == FileFormat.ANIM_SINGLE:
            return AnimSingleDecoder(fp).decode()
        elif file_format == FileFormat.ANIM_MULTIPLE:
            return AnimMultiDecoder(fp).decode()
        elif file_format == FileFormat.PIC_MULTIPLE:
            return PicMultiDecoder(fp).decode()
        elif file_format == FileFormat.ANIM_MULTIPLE_64:
            return AnimMulti64Decoder(fp).decode()
