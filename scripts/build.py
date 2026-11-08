#!/usr/bin/env python3
"""
ByteSift Standalone Application Packaging Script
Builds standalone, zero-dependency executable packages using PyInstaller.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)

    print("=" * 60)
    print("ByteSift Standalone Application Builder")
    print(f"Working Directory: {root_dir}")
    print(f"Platform: {sys.platform}")
    print("=" * 60)

    # Verify PyInstaller is installed
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[!] PyInstaller is not installed. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    assets_dir = root_dir / "bytesift" / "assets"
    dist_dir = root_dir / "dist"
    entry_point = root_dir / "bytesift" / "__main__.py"

    # Set up data separator (: on POSIX, ; on Windows)
    data_sep = ";" if sys.platform.startswith("win") else ":"
    add_data_arg = f"{assets_dir}{data_sep}bytesift/assets"

    if sys.platform.startswith("win"):
        icon_path = assets_dir / "icon_light.ico"
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name", "ByteSift-Windows-x64",
            "--icon", str(icon_path),
            "--add-data", add_data_arg,
            str(entry_point),
        ]
        print("\n[*] Executing Windows Build:")
        print(" ".join(cmd))
        subprocess.check_call(cmd)

        # Copy to ByteSift.exe for convenience
        src_exe = dist_dir / "ByteSift-Windows-x64.exe"
        dest_exe = dist_dir / "ByteSift.exe"
        if src_exe.exists():
            shutil.copyfile(src_exe, dest_exe)
            print(f"\n[+] Created: {src_exe}")
            print(f"[+] Created mirror: {dest_exe}")

    elif sys.platform == "darwin":
        icon_path = assets_dir / "icon_light.png"
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name", "ByteSift",
            "--icon", str(icon_path),
            "--osx-bundle-identifier", "com.bytesift.app",
            "--add-data", add_data_arg,
            str(entry_point),
        ]
        print("\n[*] Executing macOS Build:")
        print(" ".join(cmd))
        subprocess.check_call(cmd)

        app_bundle = dist_dir / "ByteSift.app"
        dmg_path = dist_dir / "ByteSift-macOS-Universal.dmg"
        if app_bundle.exists() and shutil.which("hdiutil"):
            print("\n[*] Creating Apple Disk Image (.dmg)...")
            dmg_root = root_dir / "dmg_root"
            if dmg_root.exists():
                shutil.rmtree(dmg_root, ignore_errors=True)
            dmg_root.mkdir(exist_ok=True)
            shutil.copytree(app_bundle, dmg_root / "ByteSift.app", dirs_exist_ok=True)
            app_symlink = dmg_root / "Applications"
            if not app_symlink.exists():
                os.symlink("/Applications", app_symlink)
            subprocess.check_call([
                "hdiutil", "create",
                "-volname", "ByteSift",
                "-srcfolder", str(dmg_root),
                "-ov",
                "-format", "UDZO",
                str(dmg_path),
            ])
            shutil.copyfile(dmg_path, dist_dir / "ByteSift.dmg")
            print(f"[+] Created DMG: {dmg_path}")
            shutil.rmtree(dmg_root, ignore_errors=True)

        if app_bundle.exists() and shutil.which("ditto"):
            zip_path = dist_dir / "ByteSift-macOS.zip"
            subprocess.check_call(["ditto", "-c", "-k", "--keepParent", str(app_bundle), str(zip_path)])
            print(f"[+] Created ZIP: {zip_path}")

    else:
        # Linux
        icon_path = assets_dir / "icon_light.png"
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name", "ByteSift-Linux-x86_64",
            "--icon", str(icon_path),
            "--add-data", add_data_arg,
            str(entry_point),
        ]
        print("\n[*] Executing Linux Build:")
        print(" ".join(cmd))
        subprocess.check_call(cmd)

    print("\n[+] Packaging completed successfully. Artifacts available in ./dist/")


if __name__ == "__main__":
    main()
