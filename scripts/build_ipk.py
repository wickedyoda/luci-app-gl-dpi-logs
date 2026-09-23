#!/usr/bin/env python3
"""
Build .ipk for GL.iNet OpenWrt 21.02 (opkg 2021-06-13)
Format: gzip-compressed tar (NOT ar archive)
Outer: gzip(mtime=0, os=3, xfl=0) wrapping tar
  ├── debian-binary (file: "2.0\n")
  ├── control.tar.gz (gzip tar w/ gzip os=3)
  │   ├── ./control (Package metadata)
  │   └── ./postinst (mkdir dirs)
  └── data.tar.gz (gzip tar w/ gzip os=3)
      ├── ./dir entries (explicit dirs)
      └── ./file entries (all paths ./ prefixed)
"""
import gzip
import io
import os
import sys
import tarfile

PKG_NAME = sys.argv[1] if len(sys.argv) > 1 else "luci-app-gl-dpi-logs-v1.01"
PKG_VERSION = sys.argv[2] if len(sys.argv) > 2 else "1.0.1"
OUTPUT_IPK = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/{PKG_NAME}_{PKG_VERSION}_all.ipk"
SRC_DIR = sys.argv[4] if len(sys.argv) > 4 else "/tmp/pkgbuild_final"

# ── control.tar.gz ──
CONTROL_CONTENT = f"""Package: {PKG_NAME}
Version: {PKG_VERSION}
Section: luci
Architecture: all
Maintainer: WickedYoda
Depends: luci-base, luci-lib-jsonc
Description: LuCI app for exporting DPI and content filtering logs from GL.iNet routers
 This app reads QoS and content protection statistics from GL.iNet routers,
 displays them in the LuCI web UI, and allows export to JSON or CSV format.
"""

POSTINST = b"#!/bin/sh\nmkdir -p /usr/lib/lua/luci/view/gl-dpi-logs\nmkdir -p /usr/lib/lua/luci/model/cbi/gl-dpi-logs\nexit 0\n"
DEBIAN_BINARY = b"2.0\n"

ctrl_buf = io.BytesIO()
with tarfile.open(fileobj=ctrl_buf, mode="w:gz") as tar:
    info = tarfile.TarInfo(name="./control")
    info.size = len(CONTROL_CONTENT.encode()); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
    tar.addfile(info, io.BytesIO(CONTROL_CONTENT.encode()))
    pinfo = tarfile.TarInfo(name="./postinst")
    pinfo.size = len(POSTINST); pinfo.mode = 0o755; pinfo.mtime = 0; pinfo.uid = 0; pinfo.gid = 0
    tar.addfile(pinfo, io.BytesIO(POSTINST))
control_tgz = ctrl_buf.getvalue()

# ── data.tar.gz ──
data_buf = io.BytesIO()
with tarfile.open(fileobj=data_buf, mode="w:gz") as tar:
    all_dirs = set()
    files_to_add = []
    for root, dirs, files in os.walk(SRC_DIR):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            arcname = "./" + os.path.relpath(fpath, SRC_DIR)
            files_to_add.append((fpath, arcname))
            parts = arcname.split("/")
            for i in range(2, len(parts)):
                all_dirs.add("/".join(parts[:i]))
    for dirpath in sorted(all_dirs):
        dinfo = tarfile.TarInfo(name=dirpath)
        dinfo.type = tarfile.DIRTYPE; dinfo.mode = 0o755; dinfo.mtime = 0; dinfo.uid = 0; dinfo.gid = 0
        tar.addfile(dinfo)
    for fpath, arcname in sorted(files_to_add, key=lambda x: x[1]):
        info = tar.gettarinfo(fpath, arcname=arcname)
        info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""; info.mtime = 0
        with open(fpath, "rb") as f:
            tar.addfile(info, f)
data_tgz = data_buf.getvalue()

# ── outer gzip tar ──
ipk_buf = io.BytesIO()
with tarfile.open(fileobj=ipk_buf, mode="w") as tar:
    for name, data in [("./debian-binary", DEBIAN_BINARY), ("./control.tar.gz", control_tgz), ("./data.tar.gz", data_tgz)]:
        info = tarfile.TarInfo(name=name)
        info.size = len(data); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
        tar.addfile(info, io.BytesIO(data))
tar_data = ipk_buf.getvalue()

# gzip with Unix OS, default compression (XFL=0)
ipk_buf2 = io.BytesIO()
with gzip.GzipFile(fileobj=ipk_buf2, mode="wb", mtime=0, compresslevel=6) as gz:
    gz.write(tar_data)
ipk_data = ipk_buf2.getvalue()
# Force XFL=0 (default), OS=3 (Unix)
ipk_data = ipk_data[:8] + b"\x00\x03" + ipk_data[10:]

with open(OUTPUT_IPK, "wb") as f:
    f.write(ipk_data)

print(f"✅ Built: {OUTPUT_IPK} ({len(ipk_data)} bytes)")
print(f"   Magic: {ipk_data[:3].hex(' ')} (gzip)")
