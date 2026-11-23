# Changes

## 1.1 (2026-11-23)

- The device is built on GitHub from this repository's source: the external for macOS (Intel and Apple Silicon, in one
  file) and Windows (64-bit), packed into `Grids.amxd` by `tools/amxd.py`.
- The external uses Max's current entry point (`ext_main`).
- Windows: the random numbers behind Chaos use `rand_s`, which is now properly declared.
- The 32-bit Windows external is gone (current Live is 64-bit only).

## 1.0 (2026-11-23)

- The project moves to [w0ts](https://w0ts.github.io/), with its site at
  [w0ts.github.io/Grids-for-Max-for-Live](https://w0ts.github.io/Grids-for-Max-for-Live/).
- `Grids.amxd` is the device as published before on motscousus.com and maxforlive.com (with Apple Silicon support).

## 2014

- 2014-09-26: code clean-up, several instances work together, a better UI.
- 2014-09-25: euclidean mode fixed, a reset added.
- 2014-09-24: the code reworked, changes in the UI.
- 2014-09-23: rewritten as a C external, which fixes the sync.
- 2014-09-18: the first version, in JavaScript.
