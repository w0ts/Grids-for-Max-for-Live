# SPDX-License-Identifier: GPL-3.0-or-later
"""tools/amxd.py: a device file read and written back is the same bytes; build() makes a device that holds the
patcher, its pictures, the macOS external three ways and the Windows one, and nothing else.

    python3 -m unittest discover -s tests"""
import importlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))      # (tools/ is not a package)
amxd = importlib.import_module("amxd")


def fake_mxo(root: Path) -> Path:
    mxo = root / "grids.mxo"
    (mxo / "Contents" / "MacOS").mkdir(parents=True)
    (mxo / "Contents" / "MacOS" / "grids").write_bytes(b"\xca\xfe\xba\xbe" + b"x" * 60)
    (mxo / "Contents" / "MacOS" / "grids").chmod(0o755)
    (mxo / "Contents" / "Info.plist").write_bytes(b"<plist/>")
    (mxo / "Contents" / "PkgInfo").write_bytes(b"iLaX????")
    return mxo


class AmxdTest(unittest.TestCase):
    def test_roundtrip_is_byte_identical(self):
        dev = amxd.Device(head=((b"ampf", b"mmmm"), (b"meta", struct.pack("<I", 7))),
                          entries=(amxd.Entry(b"JSON", "Grids.amxd", b'{"patcher":{}}\n\0', flag=17),
                                   amxd.Entry(b"mx64", "grids.mxe64", b"MZ" + b"\1" * 33)))
        blob = amxd.write(dev)
        self.assertEqual(amxd.read(blob), dev)
        self.assertEqual(amxd.write(amxd.read(blob)), blob)

    def test_names_are_nul_padded_to_four_bytes(self):
        for name, size in (("Grids.amxd", 12), ("grids.mxe64", 12), ("Untitled.png", 16), ("grids/executable", 20)):
            self.assertEqual(len(amxd._padded(name)), size, name)

    def test_not_a_device_is_refused(self):
        with self.assertRaises(ValueError):
            amxd.read(b"ampf\x04\x00\x00\x00mmmmptch\x04\x00\x00\x00nope")

    def test_build_holds_the_patcher_pictures_and_both_externals(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mxe64 = d / "grids.mxe64"
            mxe64.write_bytes(b"MZ" + b"\0" * 62)
            blob = amxd.build(fake_mxo(d), mxe64, ROOT / "device" / "patcher.json", ROOT / "device" / "media")
        dev = amxd.read(blob)
        names = [e.name for e in dev.entries]
        self.assertEqual(names, ["Grids.amxd", "Untitled.png", "grids.mxo", "grids/zipfile", "grids/executable",
                                 "grids/plist", "grids.mxe64"])
        self.assertEqual(dict(dev.head)[b"ampf"], b"mmmm")
        patcher = dev.entries[0].data
        self.assertTrue(patcher.endswith(b"\0"))
        self.assertIn("patcher", json.loads(patcher.rstrip(b"\0")))
        zipped = zipfile.ZipFile(io.BytesIO(dev.entries[3].data)).namelist()
        self.assertIn("grids.mxo/Contents/MacOS/grids", zipped)
        self.assertFalse(any(n.startswith("__MACOSX") for n in zipped))
        self.assertEqual(dev.entries[4].data[:4], b"\xca\xfe\xba\xbe")
        self.assertEqual(dev.entries[6].kind, b"mx64")
        self.assertEqual(amxd.write(dev), blob)


if __name__ == "__main__":
    unittest.main()
