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
        version_file = root_dir / "scripts" / "version_info.txt"
        iss_path = root_dir / "scripts" / "installer.iss"

        # 1. Build Onedir directory bundle (required for clean Inno Setup installer)
        cmd_dir = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--windowed",
            "--name", "ByteSift",
            "--icon", str(icon_path),
            "--add-data", add_data_arg,
        ]
        if version_file.exists():
            cmd_dir.extend(["--version-file", str(version_file)])
        cmd_dir.append(str(entry_point))

        print("\n[*] Executing Windows Directory Build (Clean Onedir):")
        print(" ".join(cmd_dir))
        subprocess.check_call(cmd_dir)

        # Mirror assets to dist/ByteSift/bytesift/assets so shortcuts and onedir always find them
        onedir_assets = dist_dir / "ByteSift" / "bytesift" / "assets"
        onedir_assets.mkdir(parents=True, exist_ok=True)
        for item in assets_dir.glob("*"):
            shutil.copy2(item, onedir_assets / item.name)

        # 2. Build Single-file portable executable
        cmd_onefile = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name", "ByteSift-Windows-x64",
            "--icon", str(icon_path),
            "--add-data", add_data_arg,
        ]
        if version_file.exists():
            cmd_onefile.extend(["--version-file", str(version_file)])
        cmd_onefile.append(str(entry_point))

        print("\n[*] Executing Windows Standalone Executable Build:")
        print(" ".join(cmd_onefile))
        subprocess.check_call(cmd_onefile)

        src_exe = dist_dir / "ByteSift-Windows-x64.exe"
        dest_exe = dist_dir / "ByteSift.exe"
        if src_exe.exists():
            shutil.copyfile(src_exe, dest_exe)
            print(f"\n[+] Created: {src_exe}")
            print(f"[+] Created mirror: {dest_exe}")

        # 3. Package Directory into ZIP Archive (Portable Bundle)
        zip_path = dist_dir / "ByteSift-Windows-x64.zip"
        onedir_path = dist_dir / "ByteSift"
        if onedir_path.is_dir():
            print("\n[*] Creating Portable ZIP Archive...")
            import zipfile
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(onedir_path):
                    for file in files:
                        full_path = Path(root) / file
                        arcname = full_path.relative_to(dist_dir)
                        zf.write(full_path, arcname=str(arcname))
                if (root_dir / "README.md").exists():
                    zf.write(root_dir / "README.md", arcname="ByteSift/README.md")
                if (root_dir / "LICENSE").exists():
                    zf.write(root_dir / "LICENSE", arcname="ByteSift/LICENSE.txt")
            print(f"[+] Created Portable ZIP package: {zip_path}")

        # 4. Compile Inno Setup Installer (if ISCC is present)
        iscc_path = shutil.which("iscc") or shutil.which("ISCC.exe")
        if not iscc_path:
            for potential_path in [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
                r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            ]:
                if Path(potential_path).exists():
                    iscc_path = potential_path
                    break

        if iscc_path and iss_path.exists() and onedir_path.is_dir():
            print(f"\n[*] Found Inno Setup Compiler: {iscc_path}")
            print("[*] Compiling Windows Setup Installer Wizard...")
            app_version = "0.1.8"
            init_file = root_dir / "bytesift" / "__init__.py"
            if init_file.exists():
                for line in init_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("__version__"):
                        app_version = line.split("=")[1].strip().strip('"\'')
                        break
            subprocess.check_call([iscc_path, f"/DMyAppVersion={app_version}", str(iss_path)])
            setup_exe = dist_dir / "ByteSift-Setup-x64.exe"
            if setup_exe.exists():
                shutil.copyfile(setup_exe, dist_dir / "ByteSift-Setup.exe")
                print(f"[+] Created Windows Installer: {setup_exe}")
                print(f"[+] Created mirror: {dist_dir / 'ByteSift-Setup.exe'}")
        else:
            print("\n[-] Inno Setup compiler (ISCC) not found locally. Skipping installer compilation.")

    elif sys.platform == "darwin":
        icns_path = assets_dir / "icon_light.icns"
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name", "ByteSift",
            "--osx-bundle-identifier", "com.bytesift.app",
            "--add-data", add_data_arg,
        ]
        if icns_path.exists():
            cmd.extend(["--icon", str(icns_path)])
        cmd.append(str(entry_point))
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
