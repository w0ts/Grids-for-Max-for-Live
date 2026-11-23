# Grids for Max for Live

> ## [→ w0ts.github.io/Grids-for-Max-for-Live](https://w0ts.github.io/Grids-for-Max-for-Live/)
> **What Grids for Max for Live is, the download and how to use it: on the site.**
> This README is for developers.

The C external at the heart of the Max for Live device: a port of the code of
[Mutable Instruments Grids](https://github.com/pichenettes/eurorack/tree/master/grids), the topographic drum sequencer
by Émilie Gillet. The device itself (`Grids.amxd`, with the external inside) is attached to the
[releases](https://github.com/w0ts/Grids-for-Max-for-Live/releases/latest).

## Layout

| Path | What |
|---|---|
| `grids.c`, `resources.h` | The external: the pattern maps, the drum and euclidean modes, the note outputs |
| `CMakeLists.txt` | Builds it with the Max SDK (`max-sdk-base`, fetched at a pinned commit) |
| `device/` | The device's source: its patcher (`patcher.json`) and picture (`media/`) |
| `tools/amxd.py` | Reads and writes `.amxd` files; packs `Grids.amxd` from `device/` and the built externals |
| `tests/` | The packer's tests (`python3 -m unittest discover -s tests`) |
| `grids.maxhelp` | The external's Max help patch |
| `site/` | The user site, deployed by `.github/workflows/pages.yml` |

## Build

```
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

The external lands in `build/package/externals/`: `grids.mxo` on macOS (x86_64 + arm64, signed ad hoc), `grids.mxe64`
on Windows. With both, pack the device:

```
python3 tools/amxd.py build --mxo build/package/externals/grids.mxo --mxe64 path/to/grids.mxe64 --out Grids.amxd
```

`.github/workflows/build.yml` does all of it on every push: both externals, then `Grids.amxd` as a build artifact.
To release, push a `v*` tag: the workflow creates the release if needed and attaches its `Grids.amxd`.

To change the device itself, open `Grids.amxd` in Max, edit, freeze and save, then put its patcher back into
`device/patcher.json` (`tools/amxd.py list` shows what a device holds; `amxd.read()` gives the JSON entry).

GPL-3.0 ([LICENSE](LICENSE)), as the original Grids code.
