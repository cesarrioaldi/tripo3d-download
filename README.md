# Tripo 3D Downloader

**[English](README.md) · [Bahasa Indonesia](README.id.md)**

Download 3D models from [studio.tripo3d.ai](https://studio.tripo3d.ai/3d-model-gallery)
**without spending credits**. Desktop GUI plus a CLI for servers and scripts.
Runs on Windows, macOS, and Linux.

```
        ┌──────────────────────────────────────────────┐
        │  Tripo 3D Downloader                         │
        │  ┌────────────────────────────────────────┐  │
        │  │ paste model URLs (one per line)        │  │
        │  └────────────────────────────────────────┘  │
        │  Folder: ~/Downloads/tripo_dl      [Browse]  │
        │  Format: [Auto (native) ▾]                │
        │                                [ Download ]  │
        │  ┌─────────────┬───────────────┬──────────┐  │
        │  │ Model       │ Status        │ Size     │  │
        │  │ dragon      │ ...glb — OK   │ 23.7 MB  │  │
        │  └─────────────┴───────────────┴──────────┘  │
        └──────────────────────────────────────────────┘
```

## Why does this not cost credits?

Each model page ships the original asset URL (a signed CloudFront URL) inside its
Nuxt payload (`model_url`). That URL can simply be fetched — no login, no cookies,
and **no credit deducted**. Credits are only charged by the _Export_ button inside
the Tripo app, and this tool never touches the export API.

Export is still the only way to get other formats straight from Tripo. When you
pick a different format here, the conversion happens **locally with Blender**.

## Requirements

| Part | Needs | Notes |
|---|---|---|
| All download features | Python 3.9+ and `curl_cffi` | CLI & GUI |
| GUI | `tkinter` | bundled with Python on Windows & macOS; a package on Linux |
| Format conversion (FBX/OBJ/STL) | Blender 3.x/4.x | optional, only for non-native formats |
| `meshopt` GLB → conversion | Node.js (`npx`) | used automatically to decode |

## Install

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/) — tick **Add python.exe to PATH**.
2. Download this repo (Code → Download ZIP, then extract).
3. Double-click **`install.bat`** (creates `.venv`, installs deps, opens the GUI).

After that, just double-click **`Tripo DL.bat`**.

### macOS

```bash
git clone https://github.com/cesarrioaldi/tripo3d-download tripo-dl && cd tripo-dl
bash install.sh
./run.sh
```

`tkinter` ships with Python from python.org and Homebrew. If you hit a tkinter
error: `brew install python-tk`.

### Linux

```bash
sudo apt install python3-tk python3-venv   # Debian/Ubuntu (Fedora: python3-tkinter)
git clone https://github.com/cesarrioaldi/tripo3d-download tripo-dl && cd tripo-dl
bash install.sh
./run.sh
```

Without a venv:

```bash
pip install -r requirements.txt
python3 tripo_app.py
```

### What about the UI on other OSes?

No separate UI is needed. The GUI is **tkinter**, part of Python on all three
platforms, so it looks and behaves the same on Windows, macOS, and Linux. The only
difference is installing `tkinter` on Linux (`python3-tk`, one line above). On
machines without a display (SSH/VPS/CI) use the CLI — same engine, no tkinter.

## Usage — GUI

1. Launch the app (`Tripo DL.bat` on Windows, `./run.sh` on macOS/Linux).
2. Open a model page in your browser, copy its URL, paste it into the top box
   (many at once is fine, one per line).
3. Pick the output folder (default `~/Downloads/tripo_dl`).
4. Pick a **Format**: keep `Auto (native)` if you don't need conversion.
5. Hit **Download**. Per-model status shows up in the table.

URLs from `tripo3d.ai` or `www.tripo3d.ai` are rewritten to `studio.tripo3d.ai`
automatically (only that domain serves the model pages).

## Usage — CLI

```bash
python tripo_cli.py <url> [<url> ...] [-o folder] [-f auto|glb|fbx|obj|stl]

# examples
python tripo_cli.py "https://studio.tripo3d.ai/3d-model/some-model-<uuid>" -o ~/Downloads/tripo_dl
python tripo_cli.py url1 url2 -f fbx -o ./models
```

Exit code `0` when everything succeeded, `1` if anything failed — safe for scripts.

## Formats & conversion

| Option | What happens |
|---|---|
| `Auto (native)` | saves whatever the server serves: usually `.glb`, sometimes `.fbx` |
| `GLB` / `FBX` / `OBJ` / `STL` | downloads the native file, then converts locally with Blender |

Conversion notes:

- Blender is auto-detected (PATH, common per-OS locations). If it isn't found, set
  `BLENDER_PATH=/path/to/blender`.
- Tripo GLBs use `EXT_meshopt_compression`, which Blender cannot read. The tool
  detects this and decodes it first through `npx @gltf-transform/cli` (needs
  Node.js). Without Node, GLB conversion fails with a clear message.
- Conversion keeps textures/materials wherever possible; STL has none by design.

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `HTTP 404` | URL isn't from `studio.tripo3d.ai`, or the model was deleted/made private |
| `Cloudflare challenge page` | Cloudflare challenge served; click Download again (usually passes) |
| `Missing dependency` | `pip install curl_cffi` |
| `No module named tkinter` | Linux: `sudo apt install python3-tk`; macOS: `brew install python-tk` |
| `Blender tidak ditemukan` (Blender not found) | install Blender or set `BLENDER_PATH` |
| `butuh Node.js (npx)` (needs Node.js) | install Node.js, or use format `Auto` |
| `format tidak dikenali` (unknown format) | the server returned something that isn't a 3D model; check the URL |
| Leftover `.part` file | download was interrupted; the file is cleaned up automatically, just retry |

## Layout

```
tripo_app.py      GUI + engine (fetch, extract, download, convert)
tripo_cli.py      CLI using the same engine
tripo_convert.py  Blender-side conversion script
requirements.txt  curl_cffi
install.sh/.bat   per-OS installers
run.sh            GUI launcher (macOS/Linux)
Tripo DL.bat      GUI launcher (Windows)
```

## Limitations

- Only fetches assets that are published in Tripo's public gallery.
- Asset URLs are signed and expire (~24h). The tool always pulls a fresh URL from
  the page at that moment, so normal use is unaffected.
- Other server-side formats (e.g. USDZ) remain export-only via Tripo.

3D assets remain the property of their respective creators. Use responsibly.
