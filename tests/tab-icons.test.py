"""Checks native tab icon assets used by the mini-program."""
import json
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class TabIconChecks(unittest.TestCase):
    def test_all_tab_assets_are_transparent_and_use_consistent_colors(self):
        pages = json.loads((ROOT / 'src' / 'pages.json').read_text())
        self.assertEqual(len(pages['tabBar']['list']), 3)
        for item in pages['tabBar']['list']:
            alpha_masks = []
            for key in ('iconPath', 'selectedIconPath'):
                path = ROOT / 'src' / item[key]
                self.assertLess(path.stat().st_size, 40 * 1024)
                image = Image.open(path).convert('RGBA')
                self.assertEqual(image.size, (128, 128))
                self.assertEqual(image.getpixel((0, 0))[3], 0)
                self.assertEqual(image.getpixel((127, 127))[3], 0)
                alpha_masks.append(image.getchannel('A').tobytes())
                data = image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()
                pixels = [pixel for pixel in data if pixel[3] > 245]
                self.assertTrue(pixels)
                if key == 'selectedIconPath':
                    self.assertTrue(any(r > g * 1.8 and r > b * 1.5 for r, g, b, _ in pixels))
                else:
                    self.assertTrue(all(abs(r-g) < 20 and abs(g-b) < 20 for r, g, b, _ in pixels))
            self.assertEqual(alpha_masks[0], alpha_masks[1], item['pagePath'])


if __name__ == '__main__':
    unittest.main()
