"""Draw the native mini-program tab icons at high resolution.

Run with Python and Pillow installed. All six assets use the same geometry,
with brand red for the selected state and neutral grey for the normal state.
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUTPUT = Path(__file__).resolve().parents[1] / 'src' / 'static' / 'tab'
SCALE = 4
SIZE = 128
NORMAL = '#737985'
ACTIVE = '#cc3d35'


def points(coords):
    return [(int(x * SCALE), int(y * SCALE)) for x, y in coords]


def draw_icon(name, selected):
    color = ACTIVE if selected else NORMAL
    canvas = Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    stroke = 8 * SCALE
    if name == 'home':
        draw.line(points([(17, 57), (64, 17), (111, 57)]), fill=color, width=stroke, joint='curve')
        draw.line(points([(27, 50), (27, 106), (52, 106), (52, 75), (76, 75), (76, 106), (101, 106), (101, 50)]), fill=color, width=stroke, joint='curve')
    elif name == 'electronic':
        draw.rounded_rectangle((20*SCALE, 20*SCALE, 108*SCALE, 108*SCALE), radius=13*SCALE, outline=color, width=stroke)
        draw.ellipse((69*SCALE, 36*SCALE, 84*SCALE, 51*SCALE), fill=color)
        draw.line(points([(27, 88), (48, 66), (63, 80), (76, 68), (101, 92)]), fill=color, width=stroke, joint='curve')
    else:
        draw.ellipse((46*SCALE, 17*SCALE, 82*SCALE, 53*SCALE), outline=color, width=stroke)
        draw.arc((27*SCALE, 58*SCALE, 101*SCALE, 130*SCALE), start=180, end=360, fill=color, width=stroke)
        draw.line(points([(27, 94), (27, 105), (101, 105), (101, 94)]), fill=color, width=stroke, joint='curve')
    return canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for icon in ('home', 'electronic', 'profile'):
        draw_icon(icon, False).save(OUTPUT / f'{icon}1.png', optimize=True)
        draw_icon(icon, True).save(OUTPUT / f'{icon}_pink.png', optimize=True)
