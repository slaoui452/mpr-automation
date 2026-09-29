"""Regenerates app/ui/theme/icons/app.ico (the .exe icon) from the logo drawn in logo_mark.py.

Usage, from the project root:  .venv\\Scripts\\python.exe tools\\make_icon.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice  # noqa: E402
from PyQt5.QtGui import QGuiApplication  # noqa: E402

from app.ui.widgets.logo_mark import logo_pixmap  # noqa: E402

SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
TARGET = ROOT / "app" / "ui" / "theme" / "icons" / "app.ico"


def png_bytes(size: int) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    logo_pixmap(size).save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def main() -> None:
    app = QGuiApplication(sys.argv)  # noqa: F841 - painting needs an application object
    images = [png_bytes(size) for size in SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))           # reserved, type 1 = icon, count
    offset = len(header) + 16 * len(images)
    entries, payload = b"", b""
    for size, png in zip(SIZES, images):
        side = 0 if size >= 256 else size                     # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(payload))
        payload += png
    TARGET.write_bytes(header + entries + payload)
    print(f"Wrote {TARGET} ({len(SIZES)} sizes)")


if __name__ == "__main__":
    main()
