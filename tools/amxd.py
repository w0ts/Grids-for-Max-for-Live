#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read and write a frozen Max for Live device (.amxd), and build Grids.amxd from source.

    python3 tools/amxd.py list DEVICE.amxd
    python3 tools/amxd.py build --mxo grids.mxo --mxe64 grids.mxe64 --out Grids.amxd

A device file is a few chunks (4-byte tag, 4-byte little-endian length): "ampf" (the device kind, "mmmm" for a MIDI
device), "meta", then "ptch" holding a frozen bundle, "mx@c": a big-endian header (16, 0, offset of the directory), the
files one after the other, and the directory "dlst" of "dire" entries (type, fnam, sz32, of32, vers, flag, mdat; each a
tag, a big-endian length counting its 8-byte head, a payload padded with NULs to 4 bytes). Max stores a macOS external
three ways: a 4-byte placeholder named NAME.mxo (type "iLaX"), the whole bundle zipped (NAME/zipfile), and its binary
and Info.plist alone (NAME/executable, NAME/plist); a Windows one as NAME.mxe64 (type "mx64").

build assembles Grids.amxd from device/patcher.json (the patcher), device/media/ (its pictures) and the externals built
by CMake, so the released device carries exactly this repository's code. Standard library only."""
from __future__ import annotations

import argparse
import io
import struct
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MDAT = bytes.fromhex("df781620")      # a fixed modification stamp: the build is reproducible


@dataclass(frozen=True)
class Entry:
    kind: bytes        # 4 bytes: b"JSON", b"PNG ", b"iLaX", b"mx64", b"\0\0\0\0" ...
    name: str
    data: bytes
    vers: int = 0
    flag: int = 0
    mdat: bytes = MDAT


@dataclass(frozen=True)
class Device:
    head: tuple        # the chunks before "ptch": ((tag, payload), ...)
    entries: tuple


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + struct.pack(">I", 8 + len(payload)) + payload


def _padded(name: str) -> bytes:
    raw = name.encode("utf-8")
    return raw + b"\0" * (4 - len(raw) % 4)     # (always at least one NUL)


def read(blob: bytes) -> Device:
    head, i = [], 0
    while blob[i:i + 4] != b"ptch":
        tag, n = blob[i:i + 4], struct.unpack("<I", blob[i + 4:i + 8])[0]
        if not tag.isalpha() or i + 8 + n > len(blob):
            raise ValueError(f"not a device file: chunk {tag!r} at {i}")
        head.append((tag, blob[i + 8:i + 8 + n]))
        i += 8 + n
    size = struct.unpack("<I", blob[i + 4:i + 8])[0]
    mx = blob[i + 8:i + 8 + size]
    if mx[:4] != b"mx@c":
        raise ValueError("the patch is not a frozen bundle (mx@c)")
    hsize, _, dir_off = struct.unpack(">III", mx[4:16])
    dlst = mx[dir_off:]
    if dlst[:4] != b"dlst":
        raise ValueError("no directory (dlst)")
    entries, j, end = [], 8, struct.unpack(">I", dlst[4:8])[0]
    while j < end:
        n = struct.unpack(">I", dlst[j + 4:j + 8])[0]
        fields, k, body = {}, 0, dlst[j + 8:j + n]
        while k < len(body):
            tag, m = body[k:k + 4], struct.unpack(">I", body[k + 4:k + 8])[0]
            fields[tag] = body[k + 8:k + m]
            k += m
        off, sz = struct.unpack(">I", fields[b"of32"])[0], struct.unpack(">I", fields[b"sz32"])[0]
        entries.append(Entry(kind=fields[b"type"], name=fields[b"fnam"].rstrip(b"\0").decode("utf-8"),
                             data=mx[off:off + sz], vers=struct.unpack(">I", fields[b"vers"])[0],
                             flag=struct.unpack(">I", fields[b"flag"])[0], mdat=fields[b"mdat"]))
        j += n
    if hsize != 16:
        raise ValueError(f"unexpected bundle header size {hsize}")
    return Device(head=tuple(head), entries=tuple(entries))


def write(dev: Device) -> bytes:
    body, dire, off = bytearray(), bytearray(), 16
    for e in dev.entries:
        dire += _chunk(b"dire", b"".join((
            _chunk(b"type", e.kind), _chunk(b"fnam", _padded(e.name)), _chunk(b"sz32", struct.pack(">I", len(e.data))),
            _chunk(b"of32", struct.pack(">I", off)), _chunk(b"vers", struct.pack(">I", e.vers)),
            _chunk(b"flag", struct.pack(">I", e.flag)), _chunk(b"mdat", e.mdat))))
        body += e.data
        off += len(e.data)
    mx = b"mx@c" + struct.pack(">III", 16, 0, off) + bytes(body) + _chunk(b"dlst", bytes(dire))
    head = b"".join(tag + struct.pack("<I", len(p)) + p for tag, p in dev.head)
    return head + b"ptch" + struct.pack("<I", len(mx)) + mx


def zip_bundle(mxo: Path) -> bytes:
    """the .mxo bundle zipped as Max stores it (the bundle's folder at the top; no macOS metadata files)"""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted([mxo, *mxo.rglob("*")]):
            arc = (Path(mxo.name) / path.relative_to(mxo)).as_posix()
            info = zipfile.ZipInfo(arc + ("/" if path.is_dir() else ""), date_time=(2014, 9, 26, 0, 0, 0))
            binary = path.parent.name == "MacOS"    # (executable whatever the mode it came with: CI artifacts drop it)
            info.external_attr = ((0o40755 if path.is_dir() else (0o100755 if binary else 0o100644)) << 16)
            z.writestr(info, b"" if path.is_dir() else path.read_bytes())
    return out.getvalue()


def build(mxo: Path, mxe64: Path, patcher: Path, media: Path) -> bytes:
    """Grids.amxd: the patcher, its pictures, the macOS external (three ways) and the Windows one"""
    name = mxo.name[:-4]
    entries = [Entry(b"JSON", "Grids.amxd", patcher.read_bytes().rstrip(b"\0") + b"\0", flag=17)]
    entries += [Entry(b"PNG ", p.name, p.read_bytes()) for p in sorted(media.glob("*.png"))]
    entries += [Entry(b"iLaX", f"{name}.mxo", b"\0\0\0\0"),
                Entry(b"\0\0\0\0", f"{name}/zipfile", zip_bundle(mxo)),
                Entry(b"\0\0\0\0", f"{name}/executable", (mxo / "Contents" / "MacOS" / name).read_bytes()),
                Entry(b"\0\0\0\0", f"{name}/plist", (mxo / "Contents" / "Info.plist").read_bytes()),
                Entry(b"mx64", f"{name}.mxe64", mxe64.read_bytes())]
    return write(Device(head=((b"ampf", b"mmmm"), (b"meta", struct.pack("<I", 7))), entries=tuple(entries)))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("device", type=Path)
    b = sub.add_parser("build")
    b.add_argument("--mxo", type=Path, required=True)
    b.add_argument("--mxe64", type=Path, required=True)
    b.add_argument("--patcher", type=Path, default=ROOT / "device" / "patcher.json")
    b.add_argument("--media", type=Path, default=ROOT / "device" / "media")
    b.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "list":
        dev = read(a.device.read_bytes())
        print(" ".join(f"{t.decode()}={p!r}" for t, p in dev.head))
        for e in dev.entries:
            print(f"{e.kind!r:10} {len(e.data):8}  {e.name}")
        return 0
    for p in (a.mxo, a.mxe64, a.patcher, a.media):
        if not p.exists():
            print(f"amxd: missing {p}", file=sys.stderr)
            return 2
    a.out.write_bytes(build(a.mxo, a.mxe64, a.patcher, a.media))
    print(f"amxd: wrote {a.out} ({a.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
