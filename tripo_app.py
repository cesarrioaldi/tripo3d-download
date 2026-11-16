"""Tripo 3D Downloader — GUI + engine, no browser/CDP needed.

Paste model page URLs from studio.tripo3d.ai (one per line), pick output
folder, hit Download. Fetches the Nuxt payload from each page (curl_cffi
impersonates Chrome through Cloudflare) and pulls the signed asset URL
directly — no credits spent.

Deps: Python 3.9+ and curl_cffi only.  Run: python tripo_app.py
"""
import json, os, pathlib, queue, re, shutil, subprocess, sys, threading, time, tkinter as tk
from tkinter import filedialog, ttk

try:
    from curl_cffi import requests as cr
except ImportError:
    sys.exit("Missing dependency. Run:  pip install curl_cffi")

IMP = "chrome124"
NUXT_RE = re.compile(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', re.S)
UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", re.I)
DOMAIN_RE = re.compile(r"^https?://(?:www\.)?tripo3d\.ai/", re.I)
DEFAULT_OUT = str(pathlib.Path.home() / "Downloads" / "tripo_dl")


def normalize_url(u):
    """Model pages only exist on studio.tripo3d.ai; apex/www 404."""
    return DOMAIN_RE.sub("https://studio.tripo3d.ai/", u.strip())


def fetch_page(url):
    r = cr.get(url, impersonate=IMP, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    if "Just a moment" in r.text[:2000]:
        raise RuntimeError("Cloudflare challenge page — retry")
    return r.text


def extract(url, html):
    m = NUXT_RE.search(html)
    if not m:
        raise RuntimeError("no Nuxt payload in page")
    arr = json.loads(m.group(1))
    slug = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    mu = UUID_RE.search(slug)
    pid = mu.group(1) if mu else slug
    try:
        idx = arr.index(pid)
    except ValueError:
        raise RuntimeError("model id not found in payload")
    for o in arr:
        if isinstance(o, dict) and o.get("id") == idx and "model_url" in o:
            def deref(v):
                if isinstance(v, int):
                    return arr[v] if v < len(arr) else None
                return v
            file_url = deref(o["model_url"])
            name = deref(o.get("project_name")) or deref(o.get("model_name")) or pid[:8]
            if not isinstance(file_url, str) or not file_url.startswith("http"):
                raise RuntimeError("model_url missing")
            return {"url": file_url, "name": str(name).strip()}
    raise RuntimeError("model object not found in payload")


def sanitize(name):
    return re.sub(r"[^\w .-]+", "_", name.strip())[:80] or "model"


MODEL_EXTS = (".glb", ".fbx", ".obj", ".stl", ".usdz", ".usd", ".3mf", ".ply")


def sniff_ext(head, url):
    if head[:4] == b"glTF":
        return ".glb"
    if head.startswith(b"Kaydara FBX"):
        return ".fbx"
    path = url.split("?")[0].lower()
    for e in MODEL_EXTS:
        if path.endswith(e):
            return e
    return None


def download(url, dest, progress):
    """Fetch to dest; returns extension detected from header/url."""
    r = cr.get(url, impersonate=IMP, stream=True, timeout=300)
    try:
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")
        total = int(r.headers.get("content-length") or 0)
        got = 0
        head = b""
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                if not head:
                    head = chunk[:8]
                f.write(chunk)
                got += len(chunk)
                progress(got, total)
    finally:
        r.close()
    return sniff_ext(head, url)


def mb(n):
    return f"{n/1e6:.1f} MB"


def find_blender():
    cands = [os.environ.get("BLENDER_PATH"), shutil.which("blender")]
    if sys.platform == "darwin":
        cands += ["/Applications/Blender.app/Contents/MacOS/Blender"]
    elif sys.platform == "win32":
        cands += [r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
                  str(pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Blender Foundation/Blender 4.2/blender.exe")]
    else:
        cands += ["/usr/bin/blender", "/snap/bin/blender", "/var/lib/flatpak/exports/bin/org.blender.Blender"]
    for c in cands:
        if c and pathlib.Path(c).exists():
            return c
    return None


def convert(src, dst):
    exe = find_blender()
    if not exe:
        raise RuntimeError("Blender tidak ditemukan (set BLENDER_PATH)")
    script = pathlib.Path(__file__).with_name("tripo_convert.py")
    src = pathlib.Path(src)
    tmp = None
    try:
        if src.suffix.lower() in (".glb", ".gltf") and b"EXT_meshopt_compression" in src.open("rb").read(262144):
            npx = shutil.which("npx")
            if not npx:
                raise RuntimeError("butuh Node.js (npx) untuk decode meshopt")
            tmp = pathlib.Path(str(dst) + ".plain.glb")
            cmd = [npx, "--yes", "@gltf-transform/cli@4", "copy", str(src), str(tmp)]
            if sys.platform == "win32":
                cmd = ["cmd", "/c"] + cmd
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if r.returncode != 0 or not tmp.exists():
                raise RuntimeError("decode meshopt gagal")
            src = tmp
        r = subprocess.run([exe, "-b", "--python", str(script), "--", str(src), str(dst)],
                           capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not pathlib.Path(dst).exists():
            tail = (r.stdout + r.stderr).strip().splitlines()[-2:]
            raise RuntimeError("convert gagal: " + " | ".join(tail)[:90])
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def fetch_to(url, outdir, want=None, log=print):
    """Download one model page into outdir. Returns the saved Path (or existing one)."""
    url = normalize_url(url)
    info = extract(url, fetch_page(url))
    stem = sanitize(info["name"])
    log(f"{stem}")
    existing = next((pathlib.Path(outdir) / (stem + e)
                     for e in ((f".{want}",) if want else MODEL_EXTS)
                     if (pathlib.Path(outdir) / (stem + e)).exists()), None)
    if existing:
        log(f"{existing.name} — already on disk, skip")
        return existing
    tmp = pathlib.Path(outdir) / (stem + ".part")
    try:
        ext = download(info["url"], tmp, lambda got, tot: log(f"{stem} — {mb(got)}" + (f" / {mb(tot)}" if tot else "")))
        if not ext:
            raise RuntimeError("format tidak dikenali")
        dest = pathlib.Path(outdir) / (stem + ext)
        tmp.replace(dest)
        if want and ext.lstrip(".") != want:
            log(f"{stem} — konversi ke {want.upper()}...")
            tgt = pathlib.Path(outdir) / (stem + "." + want)
            convert(dest, tgt)
            if not tgt.exists() or tgt.stat().st_size == 0:
                raise RuntimeError("konversi gagal")
            dest.unlink()
            dest = tgt
        return dest
    finally:
        if tmp.exists():
            tmp.unlink()


class App:
    def __init__(self, root):
        self.root = root
        root.title("Tripo 3D Downloader")
        root.geometry("760x480")
        self.q = queue.Queue()

        ttk.Label(root, text="Paste model page URLs (one per line):").pack(anchor="w", padx=10, pady=(10, 2))
        self.txt = tk.Text(root, height=7, wrap="none")
        self.txt.pack(fill="x", padx=10)

        row = ttk.Frame(root); row.pack(fill="x", padx=10, pady=6)
        ttk.Label(row, text="Folder:").pack(side="left")
        self.dirvar = tk.StringVar(value=DEFAULT_OUT)
        ttk.Entry(row, textvariable=self.dirvar).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Browse", command=self.browse).pack(side="left")
        ttk.Button(row, text="Paste", command=self.paste).pack(side="left", padx=(6, 0))

        self.dlbtn = ttk.Button(row, text="Download", command=self.start, width=14)
        self.dlbtn.pack(side="right")

        fmtrow = ttk.Frame(root); fmtrow.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(fmtrow, text="Format:").pack(side="left")
        self.fmtvar = tk.StringVar(value="Auto (asli)")
        ttk.Combobox(fmtrow, textvariable=self.fmtvar, state="readonly", width=14,
                     values=("Auto (asli)", "GLB", "FBX", "OBJ", "STL")).pack(side="left", padx=6)
        self.fmtnote = ttk.Label(fmtrow, text="format lain dikonversi lokal (Blender)", foreground="#888")
        self.fmtnote.pack(side="left", padx=6)

        cols = ("name", "status", "size")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=10)
        self.tree.heading("name", text="Model"); self.tree.heading("status", text="Status"); self.tree.heading("size", text="Size")
        self.tree.column("name", width=420); self.tree.column("status", width=220); self.tree.column("size", width=90)
        vsb = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 6))
        vsb.pack(side="left", fill="y", pady=(0, 6))

        self.stat = ttk.Label(root, text="")
        self.stat.pack(anchor="w", padx=10, pady=(0, 8))
        self.busy = False

        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.after(100, self.pump)

    def browse(self):
        d = filedialog.askdirectory(initialdir=self.dirvar.get() or str(pathlib.Path.home()))
        if d:
            self.dirvar.set(d)

    def paste(self):
        try:
            clip = self.root.clipboard_get()
        except tk.TclError:
            clip = ""
        if clip:
            self.txt.insert("end", clip + "\n")

    def urls(self):
        out = []
        for line in self.txt.get("1.0", "end").splitlines():
            line = line.strip()
            if line.startswith("http") and "/3d-model/" in line:
                out.append(normalize_url(line))
        return out

    def start(self):
        urls = self.urls()
        if not urls:
            self.stat.config(text="No valid URLs (need https://studio.tripo3d.ai/3d-model/...)")
            return
        outdir = pathlib.Path(self.dirvar.get() or DEFAULT_OUT)
        outdir.mkdir(parents=True, exist_ok=True)
        self.dlbtn.config(state="disabled")
        self.busy = True
        self.tree.delete(*self.tree.get_children())
        iids = []
        for u in urls:
            iids.append(self.tree.insert("", "end", values=(u.rsplit("/", 1)[-1][:60], "queued", "")))
        threading.Thread(target=self.worker, args=(urls, outdir, iids, self.fmtvar.get()), daemon=True).start()

    def worker(self, urls, outdir, iids, fmt):
        want = None if fmt.startswith("Auto") else fmt.lower()
        n = len(urls)
        done = ok = fail = 0
        for i, (u, item) in enumerate(zip(urls, iids), 1):
            def log(msg, item=item):
                self.q.put(("row", item, msg, ""))
            try:
                dest = fetch_to(u, outdir, want, log)
                self.q.put(("row", item, f"{dest.name} — OK", mb(dest.stat().st_size)))
                ok += 1
            except Exception as e:
                self.q.put(("row", item, "FAIL: " + str(e)[:80], ""))
                fail += 1
            done += 1
            self.q.put(("stat", f"{done}/{n} done — {ok} ok, {fail} failed"))
        self.q.put(("done", f"done: {ok} ok, {fail} failed → {outdir}"))

    def pump(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "row":
                    self.tree.set(msg[1], "status", msg[2])
                    self.tree.set(msg[1], "size", msg[3])
                elif msg[0] == "stat":
                    self.stat.config(text=msg[1])
                elif msg[0] == "done":
                    self.stat.config(text=msg[1])
                    self.dlbtn.config(state="normal")
                    self.busy = False
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def quit(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    App(root)
    root.mainloop()
