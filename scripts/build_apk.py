#!/usr/bin/env python3
"""
Build .apk for OpenWrt 25.xx (Alpine APK format)
Format: gzip-compressed tar
  ├── .PKGINFO       (package metadata, key=value format)
  ├── .INSTALL       (install scripts: post-install, etc.)
  ├── .MANIFEST      (file manifest, one path per line)
  └── file entries   (usr/..., etc/... — no ./ prefix, explicit dir entries)

Usage:
  python3 build_apk.py [PKG_NAME] [PKG_VERSION] [PKG_RELEASE] [OUTPUT_APK] [SRC_DIR]
"""
import os, tarfile, io, gzip, sys

PKG_NAME = sys.argv[1] if len(sys.argv) > 1 else "luci-app-gl-dpi-logs"
PKG_VERSION = sys.argv[2] if len(sys.argv) > 2 else "1.0.1"
PKG_RELEASE = sys.argv[3] if len(sys.argv) > 3 else "0"
OUTPUT_APK = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/{PKG_NAME}-{PKG_VERSION}-r{PKG_RELEASE}-all.apk"
SRC_DIR = sys.argv[5] if len(sys.argv) > 5 else "/tmp/pkgbuild_final"

PKGINFO_CONTENT = f"""pkgname = {PKG_NAME}
pkgver = {PKG_VERSION}-r{PKG_RELEASE}
pkgdesc = LuCI app for exporting DPI and content filtering logs from GL.iNet routers
url = https://github.com/wickedyoda/luci-app-gl-dpi-logs
license = GPL-3.0-or-later
arch = all
depends = luci-base
depends = luci-lib-jsonc
maintainer = WickedYoda
"""

INSTALL_CONTENT = b"""post-install() {
\tmkdir -p /usr/lib/lua/luci/view/gl-dpi-logs
\tmkdir -p /usr/lib/lua/luci/model/cbi/gl-dpi-logs
\texit 0
}
"""


def main():
    # ── Collect file list from SRC_DIR ──
    manifest_lines = []
    all_dirs = set()
    files_to_add = []

    for root, dirs, files in os.walk(SRC_DIR):
        for fname in sorted(files):
            # Skip IPK metadata files (not installed files)
            if fname in ("control", "postinst", ".PKGINFO", ".INSTALL"):
                continue
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, SRC_DIR)
            # APK paths: no leading "./"
            arcname = relpath.lstrip("/")
            manifest_lines.append(arcname)
            files_to_add.append((fpath, arcname))
            # Collect parent directories for explicit dir entries
            parts = arcname.split("/")
            for i in range(1, len(parts)):
                all_dirs.add("/".join(parts[:i]))

    manifest = "\n".join(sorted(manifest_lines)) + "\n"

    # ── Build APK (gzip-compressed tar archive) ──
    apk_buf = io.BytesIO()
    with tarfile.open(fileobj=apk_buf, mode="w") as tar:
        # .PKGINFO — package metadata
        info = tarfile.TarInfo(name=".PKGINFO")
        info.size = len(PKGINFO_CONTENT.encode())
        info.mode = 0o644
        info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""; info.mtime = 0
        tar.addfile(info, io.BytesIO(PKGINFO_CONTENT.encode()))

        # .INSTALL — install scripts
        info = tarfile.TarInfo(name=".INSTALL")
        info.size = len(INSTALL_CONTENT)
        info.mode = 0o755
        info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""; info.mtime = 0
        tar.addfile(info, io.BytesIO(INSTALL_CONTENT))

        # .MANIFEST — file manifest
        info = tarfile.TarInfo(name=".MANIFEST")
        info.size = len(manifest.encode())
        info.mode = 0o644
        info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""; info.mtime = 0
        tar.addfile(info, io.BytesIO(manifest.encode()))

        # Explicit directory entries (for OpenWrt 25.xx apk compatibility)
        for dirpath in sorted(all_dirs):
            dinfo = tarfile.TarInfo(name=dirpath)
            dinfo.type = tarfile.DIRTYPE
            dinfo.mode = 0o755
            dinfo.uid = 0; dinfo.gid = 0; dinfo.uname = ""; dinfo.gname = ""; dinfo.mtime = 0
            tar.addfile(dinfo)

        # File entries
        for fpath, arcname in sorted(files_to_add, key=lambda x: x[1]):
            info = tar.gettarinfo(fpath, arcname=arcname)
            info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""; info.mtime = 0
            with open(fpath, "rb") as f:
                tar.addfile(info, f)

    apk_data = apk_buf.getvalue()

    # gzip with mtime=0, os=3 (Unix), XFL=0 (default compression)
    apk_buf2 = io.BytesIO()
    with gzip.GzipFile(fileobj=apk_buf2, mode="wb", mtime=0, compresslevel=6) as gz:
        gz.write(apk_data)
    apk_data = apk_buf2.getvalue()
    # Force OS=3 (Unix) in gzip trailer
    apk_data = apk_data[:9] + b"\x03" + apk_data[10:]

    with open(OUTPUT_APK, "wb") as f:
        f.write(apk_data)

    apk_size = os.path.getsize(OUTPUT_APK)
    print(f"✅ Built: {OUTPUT_APK} ({apk_size} bytes)")

    # Verify archive contents
    with tarfile.open(OUTPUT_APK, "r:gz") as tar:
        names = tar.getnames()
        pkginfo = tar.extractfile(".PKGINFO")
        if pkginfo:
            print(f"   .PKGINFO:\n{pkginfo.read().decode()}")
        print(f"   Total entries: {len(names)}")
        for n in sorted(names):
            print(f"     {n}")


if __name__ == "__main__":
    main()
