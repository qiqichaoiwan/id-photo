"""Generate simple white camera controls for native cover-image overlays."""
from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT = Path(__file__).resolve().parents[1] / 'src' / 'static' / 'camera'
SIZE = 128
SCALE = 4
WHITE = (255, 255, 255, 255)


def coords(values):
    return tuple(round(value * SCALE) for value in values)


def make_icon(name):
    canvas = Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    if name == 'album':
        draw.rounded_rectangle(coords((19, 20, 109, 108)), radius=12 * SCALE, outline=WHITE, width=7 * SCALE)
        draw.ellipse(coords((70, 37, 84, 51)), fill=WHITE)
        draw.line([coords(point) for point in ((27, 89), (48, 67), (63, 80), (77, 69), (101, 93))], fill=WHITE, width=7 * SCALE, joint='curve')
    else:
        draw.arc(coords((20, 20, 108, 108)), start=203, end=321, fill=WHITE, width=7 * SCALE)
        draw.arc(coords((20, 20, 108, 108)), start=23, end=141, fill=WHITE, width=7 * SCALE)
        draw.polygon([coords(point) for point in ((91, 17), (111, 38), (86, 40))], fill=WHITE)
        draw.polygon([coords(point) for point in ((37, 111), (17, 90), (42, 88))], fill=WHITE)
        draw.rounded_rectangle(coords((44, 48, 84, 80)), radius=5 * SCALE, outline=WHITE, width=5 * SCALE)
        draw.ellipse(coords((58, 57, 70, 69)), outline=WHITE, width=4 * SCALE)
    return canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for icon in ('album', 'switch'):
        make_icon(icon).save(OUTPUT / f'{icon}.png', optimize=True)
