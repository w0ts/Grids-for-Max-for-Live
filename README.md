# Grids for Max for Live

> ## [→ w0ts.github.io/Grids](https://w0ts.github.io/Grids/)
> **What Grids for Max for Live is, the download and how to use it: on the site.**
> This README is for developers.

The C external at the heart of the Max for Live device: a port of the code of
[Mutable Instruments Grids](https://github.com/pichenettes/eurorack/tree/master/grids), the topographic drum sequencer
by Émilie Gillet. The device itself (`Grids.amxd`, with the external inside) is attached to the
[releases](https://github.com/w0ts/Grids/releases/latest).

## Layout

| Path | What |
|---|---|
| `grids.c`, `resources.h` | The external: the pattern maps, the drum and euclidean modes, the note outputs |
| `grids.maxhelp` | Its Max help patch |
| `grids.xcodeproj`, `grids.sln`, `grids.vcxproj`, `grids.def` | The macOS and Windows projects |
| `site/` | The user site, deployed by `.github/workflows/pages.yml` |

## Build

1. Download the [Max SDK](https://github.com/Cycling74/max-sdk).
2. Copy this folder into `max-sdk/source/basics/`.
3. Create `max-sdk/build` and run `cmake -G Xcode ..` (macOS) or `cmake -G "Visual Studio 16 2019" ..` (Windows) there.
4. Open the project in `build/source/basics/grids` and build it.
5. The external is in `max-sdk/externals`.

GPL-3.0 ([LICENSE](LICENSE)), as the original Grids code.
