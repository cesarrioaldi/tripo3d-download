# Tripo 3D Downloader

Download 3D model dari [studio.tripo3d.ai](https://studio.tripo3d.ai/3d-model-gallery) **tanpa memakai credit**.
GUI untuk desktop dan CLI untuk server/script. Jalan di Windows, macOS, dan Linux.

```
        ┌──────────────────────────────────────────────┐
        │  Tripo 3D Downloader                         │
        │  ┌────────────────────────────────────────┐  │
        │  │ paste URL model (satu per baris)       │  │
        │  └────────────────────────────────────────┘  │
        │  Folder: ~/Downloads/tripo_dl      [Browse]  │
        │  Format: [Auto (asli) ▾]                  │
        │                                [ Download ]  │
        │  ┌─────────────┬───────────────┬──────────┐  │
        │  │ Model       │ Status        │ Size     │  │
        │  │ dragon      │ ...glb — OK   │ 23.7 MB  │  │
        │  └─────────────┴───────────────┴──────────┘  │
        └──────────────────────────────────────────────┘
```

## Kenapa bisa tanpa credit?

Halaman model menyimpan URL aset aslinya (signed CloudFront URL) di dalam payload
Nuxt (`model_url`). URL itu cukup dibuka langsung — tidak butuh login, tidak butuh
cookie, dan **tidak memotong credit**. Credit hanya terpotong kalau memakai tombol
_Export_ di dalam aplikasi Tripo. Program ini tidak pernah menyentuh API export.

Tombol Export tetap satu-satunya cara mendapatkan format lain dari Tripo. Kalau
kamu pilih format lain di program ini, konversi dilakukan **lokal pakai Blender**.

## Kebutuhan

| Bagian | Perlu | Catatan |
|---|---|---|
| Semua fitur download | Python 3.9+ dan `curl_cffi` | CLI & GUI |
| GUI | `tkinter` | sudah ada di Windows & macOS; Linux perlu paket |
| Konversi format (FBX/OBJ/STL) | Blender 3.x/4.x | opsional, hanya kalau memilih format selain asli |
| Model GLB ber-`meshopt` → konversi | Node.js (`npx`) | dipakai otomatis untuk decode |

## Instal

### Windows

1. Install Python dari [python.org](https://www.python.org/downloads/) — centang **Add python.exe to PATH**.
2. Download repo ini (Code → Download ZIP, lalu extract).
3. Double-click **`install.bat`** (membuat `.venv` + memasang dependensi, lalu membuka GUI).

Mulai berikutnya cukup double-click **`Tripo DL.bat`**.

### macOS

```bash
git clone <repo-url> tripo-dl && cd tripo-dl
bash install.sh
./run.sh
```

`tkinter` sudah tersedia di Python dari python.org dan Homebrew (`python-tk`). Kalau
muncul error tkinter: `brew install python-tk`.

### Linux

```bash
sudo apt install python3-tk python3-venv   # Debian/Ubuntu (Fedora: python3-tkinter)
git clone <repo-url> tripo-dl && cd tripo-dl
bash install.sh
./run.sh
```

Tanpa venv:

```bash
pip install -r requirements.txt
python3 tripo_app.py
```

### UI di OS lain — bagaimana?

Tidak perlu UI terpisah. GUI-nya **tkinter**, yang sudah jadi bagian Python di
ketiga OS, jadi tampilan dan perilakunya sama di Windows/macOS/Linux. Satu-satunya
perbedaan adalah cara memasang paket `tkinter` di Linux (`python3-tk`, satu baris
di atas). Kalau mesin tidak punya layar (SSH/VPS/CI), pakai CLI — mesin yang sama,
tanpa tkinter.

## Pakai — GUI

1. Buka aplikasi (`Tripo DL.bat` di Windows, `./run.sh` di macOS/Linux).
2. Buka halaman model di browser, copy URL-nya, paste ke kotak atas (boleh banyak, satu per baris).
3. Pilih folder hasil (default `~/Downloads/tripo_dl`).
4. Pilih **Format**: `Auto (asli)` kalau tidak perlu konversi.
5. Klik **Download**. Status per model muncul di tabel.

URL dari `tripo3d.ai` atau `www.tripo3d.ai` otomatis diarahkan ke `studio.tripo3d.ai`
(hanya domain itu yang menyajikan halaman model).

## Pakai — CLI

```bash
python tripo_cli.py <url> [<url> ...] [-o folder] [-f auto|glb|fbx|obj|stl]

# contoh
python tripo_cli.py "https://studio.tripo3d.ai/3d-model/nama-model-<uuid>" -o ~/Downloads/tripo_dl
python tripo_cli.py url1 url2 -f fbx -o ./models
```

Exit code `0` kalau semua sukses, `1` kalau ada yang gagal — aman dipakai di script.

## Format & konversi

| Pilihan | Yang terjadi |
|---|---|
| `Auto (asli)` | simpan apa adanya dari server: biasanya `.glb`, kadang `.fbx` |
| `GLB` / `FBX` / `OBJ` / `STL` | unduh aslinya dulu, lalu konversi lokal dengan Blender |

Catatan konversi:

- Blender dicari otomatis (PATH, lokasi umum per OS). Kalau tidak ketemu, set
  `BLENDER_PATH=/path/ke/blender`.
- GLB dari Tripo memakai `EXT_meshopt_compression`, yang tidak dibaca Blender.
  Program mendeteksinya lalu men-decode dulu lewat `npx @gltf-transform/cli`
  (butuh Node.js). Tanpa Node, konversi GLB akan gagal dengan pesan jelas.
- Konversi mempertahankan tekstur/material sebisa mungkin; STL memang tanpa material.

## Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `HTTP 404` | URL bukan dari `studio.tripo3d.ai`, atau modelnya sudah dihapus/private |
| `Cloudflare challenge page` | tantangan CF muncul; klik Download lagi (biasanya lolos) |
| `Missing dependency` | `pip install curl_cffi` |
| `No module named tkinter` | Linux: `sudo apt install python3-tk`; macOS: `brew install python-tk` |
| `Blender tidak ditemukan` | install Blender atau set `BLENDER_PATH` |
| `butuh Node.js (npx)` | install Node.js, atau pakai format `Auto` |
| `format tidak dikenali` | server mengirim sesuatu yang bukan model 3D; cek URL |
| File `.part` tertinggal | download terputus; file dihapus otomatis, ulangi |

## Struktur

```
tripo_app.py      GUI + engine (fetch, extract, download, convert)
tripo_cli.py      CLI, memakai engine yang sama
tripo_convert.py  script sisi Blender untuk konversi
requirements.txt  curl_cffi
install.sh/.bat   installer per OS
run.sh            launcher GUI (macOS/Linux)
Tripo DL.bat      launcher GUI (Windows)
```

## Batasan

- Hanya mengambil aset yang memang dipublikasikan di galeri publik Tripo.
- URL aset bersifat signed dan kedaluwarsa (~24 jam). Program selalu mengambil URL
  baru dari halaman saat itu juga, jadi tidak masalah untuk pemakaian normal.
- Format lain dari server (mis. USDZ) tetap hanya lewat Export resmi Tripo.

Aset 3D tetap milik pembuatnya masing-masing. Pakai dengan bijak.
