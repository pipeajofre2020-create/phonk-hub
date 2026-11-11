#!/usr/bin/env python3
"""
Phonk Hub: applies the app's name and logo to a SimpMusic checkout.

Reads marca/nombre.txt and marca/logo.png and writes every launcher icon, window icon,
installer icon and app name the Android and Windows builds use.

    python aplicar_marca.py <simpmusic checkout> <marca folder> [owner/repo]
"""

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}


def load_logo(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    return image.resize((1024, 1024), Image.LANCZOS)


def corner_color(logo: Image.Image) -> tuple:
    """Average colour of the four corners: the colour that fills around the logo on Android."""
    patch = 48
    pixels = []
    for x0, y0 in [(0, 0), (1024 - patch, 0), (0, 1024 - patch), (1024 - patch, 1024 - patch)]:
        region = logo.crop((x0, y0, x0 + patch, y0 + patch))
        pixels.extend(
            p for p in (region.getpixel((x, y)) for x in range(patch) for y in range(patch)) if p[3] > 200
        )
    if not pixels:
        return (0, 0, 0)
    return tuple(sum(p[i] for p in pixels) // len(pixels) for i in range(3))


def circle_mask(size: int, feather: float = 0.0) -> Image.Image:
    scale = 4
    big = Image.new("L", (size * scale, size * scale), 0)
    ImageDraw.Draw(big).ellipse((0, 0, size * scale - 1, size * scale - 1), fill=255)
    mask = big.resize((size, size), Image.LANCZOS)
    if feather > 0:
        inset = int(size * feather)
        small = Image.new("L", (size, size), 0)
        ImageDraw.Draw(small).ellipse((inset, inset, size - inset, size - inset), fill=255)
        mask = small.filter(ImageFilter.GaussianBlur(inset / 2))
    return mask


def rounded_mask(size: int, radius_fraction: float = 0.22) -> Image.Image:
    scale = 4
    big = Image.new("L", (size * scale, size * scale), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, size * scale - 1, size * scale - 1), radius=int(size * scale * radius_fraction), fill=255
    )
    return big.resize((size, size), Image.LANCZOS)


def masked(logo: Image.Image, size: int, mask: Image.Image) -> Image.Image:
    image = logo.resize((size, size), Image.LANCZOS)
    alpha = Image.new("L", (size, size), 0)
    alpha.paste(image.getchannel("A"), (0, 0), mask)
    image.putalpha(alpha)
    return image


def circle(logo: Image.Image, size: int) -> Image.Image:
    return masked(logo, size, circle_mask(size))


def rounded(logo: Image.Image, size: int) -> Image.Image:
    return masked(logo, size, rounded_mask(size))


def adaptive_foreground(logo: Image.Image, size: int) -> Image.Image:
    """
    The 108dp foreground layer. Launchers show only the inner 72dp and cut it to their own shape,
    so the whole logo is drawn at exactly that size; the corner colour fills any gap behind it.
    """
    inner = int(size * 72 / 108)
    art = logo.resize((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = (size - inner) // 2
    canvas.paste(art, (offset, offset), art)
    return canvas


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "\\'").replace('"', '\\"')
    )


def kotlin_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")


def ascii_name(name: str) -> str:
    """Installer package name: letters and digits only (Windows uses it for the folder and .exe)."""
    import unicodedata

    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    plain = re.sub(r"[^A-Za-z0-9]", "", plain)
    if not plain or not plain[0].isalpha():
        plain = "App" + plain
    return plain


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_in(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, lambda _: replacement, text, flags=re.MULTILINE)
    if count == 0:
        raise SystemExit(f"Pattern not found in {path}: {pattern}")
    path.write_text(new, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1])
    marca = Path(sys.argv[2])
    repo = sys.argv[3] if len(sys.argv) > 3 else ""

    name = (marca / "nombre.txt").read_text(encoding="utf-8").strip() or "Phonk Hub"
    logo = load_logo(marca / "logo.png")
    background = corner_color(logo)
    background_hex = "#{:02X}{:02X}{:02X}".format(*background)
    print(f"Nombre: {name} | paquete: {ascii_name(name)} | fondo del icono: {background_hex} | repo: {repo or '(ninguno)'}")

    # Android launcher icons
    res = root / "androidApp/src/main/res"
    for density, factor in DENSITIES.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        legacy = int(48 * factor)
        layer = int(108 * factor)
        rounded(logo, legacy).save(folder / "ic_launcher.webp", "WEBP", lossless=True)
        circle(logo, legacy).save(folder / "ic_launcher_round.webp", "WEBP", lossless=True)
        foreground = adaptive_foreground(logo, layer)
        foreground.save(folder / "ic_launcher_foreground.webp", "WEBP", lossless=True)
        foreground.save(folder / "ic_launcher_round_foreground.webp", "WEBP", lossless=True)
    circle(logo, 432).save(res / "drawable/app_icon.png")
    write_text(
        res / "values/phonk_icon_color.xml",
        f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="phonk_icon_background">{background_hex}</color>\n</resources>\n',
    )
    write_text(
        res / "values/app_name.xml",
        f"<resources>\n    <string name=\"app_name\">{xml_escape(name)}</string>\n</resources>\n",
    )
    write_text(
        root / "androidApp/src/debug/res/values/app_name.xml",
        f"<resources>\n    <string name=\"app_name\">{xml_escape(name)} Dev</string>\n</resources>\n",
    )

    # Shared resources (window icon, in-app logo, app name)
    drawable = root / "composeApp/src/commonMain/composeResources/drawable"
    rounded(logo, 432).save(drawable / "app_icon.png")
    circle(logo, 432).save(drawable / "circle_app_icon.png")
    write_text(
        root / "composeApp/src/commonMain/composeResources/values/app_name.xml",
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <string name="app_name" translatable="false">{xml_escape(name)}</string>\n</resources>\n',
    )

    # Desktop installer icons
    icons = root / "composeApp/icon"
    big_circle = circle(logo, 1024)
    big_circle.save(icons / "circle_app_icon.png")
    big_circle.save(icons / "circle_app_icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    rounded(logo, 1024).save(icons / "rounded_app_icon.png")

    # Name and repository inside the code
    brand = root / "core/common/src/commonMain/kotlin/com/maxrave/common/PhonkBrand.kt"
    replace_in(brand, r'const val NAME = ".*"', f'const val NAME = "{kotlin_escape(name)}"')
    replace_in(brand, r'const val REPO = ".*"', f'const val REPO = "{kotlin_escape(repo)}"')

    desktop = root / "desktopApp/build.gradle.kts"
    replace_in(desktop, r'packageName = "PhonkHub"', f'packageName = "{ascii_name(name)}"')
    replace_in(desktop, r'vendor = "Phonk Hub"', f'vendor = "{kotlin_escape(name)}"')
    replace_in(desktop, r'menuGroup = "Phonk Hub"', f'menuGroup = "{kotlin_escape(name)}"')
    print("Marca aplicada.")


if __name__ == "__main__":
    main()
