#!/usr/bin/env python3
"""CLI version — same engine, no GUI (headless servers, scripts, CI).

  python tripo_cli.py URL [URL ...] [-o DIR] [-f auto|glb|fbx|obj|stl]

Exit code: 0 all ok (or skipped), 1 if any failed.
"""
import argparse
import pathlib
import sys

import tripo_app as ta


def main():
    ap = argparse.ArgumentParser(description="Download studio.tripo3d.ai models without credits.")
    ap.add_argument("urls", nargs="+", help="model page URLs (apex/www auto-fixed)")
    ap.add_argument("-o", "--out", default=ta.DEFAULT_OUT, help=f"output folder (default {ta.DEFAULT_OUT})")
    ap.add_argument("-f", "--format", default="auto", choices=["auto", "glb", "fbx", "obj", "stl"],
                    help="convert to this format (needs Blender; default: native)")
    a = ap.parse_args()

    outdir = pathlib.Path(a.out).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    want = None if a.format == "auto" else a.format

    ok = fail = 0
    for i, u in enumerate(a.urls, 1):
        print(f"[{i}/{len(a.urls)}]", end=" ")
        try:
            dest = ta.fetch_to(u, outdir, want, log=lambda m: print(f"  {m}"))
            print(f"  → {dest}  ({ta.mb(dest.stat().st_size)})")
            ok += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            fail += 1

    print(f"\n{ok} ok, {fail} failed → {outdir}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
