# ByteSift ⚡

> **Lightweight, blazing-fast, 100% offline file content examiner and organizer without AI or internet.**

---

## 📖 Overview

**ByteSift** solves the messy folder problem by examining what is actually **inside** your files rather than relying solely on file extensions. It operates completely offline, without AI, external models, internet access, or third-party dependencies.

Using binary signature analysis (magic bytes), fast text content heuristics, and EXIF/metadata inspection, ByteSift classifies, deduplicates, and sorts files in milliseconds while offering a **100% reversible undo** safety net.

```
Messy Folder/
├── IMG_0041.dat        ──>  Images/JPEG/IMG_0041.dat     (Identified via Magic Bytes)
├── scan_882.pdf        ──>  Documents/Invoices_Receipts/ (Identified via Text Heuristics)
├── copy_of_photo.jpg   ──>  Duplicates/copy_of_photo.jpg (Identified via SHA-256)
└── script              ──>  Code/Python/script           (Identified via Code Signature)
```

---

## 🚀 Key Features

* **100% Offline & Private:** Zero network requests, zero telemetry, zero LLMs/cloud dependencies. All inspection happens in local memory.
* **True Content Inspection (Magic Bytes):** Detects PDFs, JPEGs, PNGs, ZIPs, Office OpenXML (`.docx`, `.xlsx`, `.pptx`), audio, video, and executables even if the file extension is wrong or missing.
* **Smart Text & Document Heuristics:** Scans text files in chunks (< 8KB) to identify Invoices, Resumes, Legal Contracts, Python/JS/HTML/SQL code, Configs, and Logs.
* **Instant Duplicate Detection:** 2-pass hashing (Size grouping + SHA-256) detects and isolates identical duplicate files into a `Duplicates/` folder.
* **One-Click Reversible Undo:** Every move is recorded in a transaction journal (`.bytesift_history.json`). Revert any session instantly with `bytesift undo`.
* **Zero Dependencies:** Pure standard library. Starts up in < 50ms and consumes < 25 MB RAM.
* **Dual Interface:** Full-featured Command Line Interface (CLI) + Native Desktop GUI (Tkinter).

---

## 🛠️ How Content Examination Works

```
                     ┌──────────────────────────┐
                     │       Input File         │
                     └────────────┬─────────────┘
                                  │
                                  ▼
               [Tier 1: Binary Magic Bytes Inspection]
          Reads initial 16-64 bytes for immutable file signatures
       (e.g., %PDF-, \xff\xd8\xff, PK\x03\x04, ID3, RIFF....WEBP)
                                  │
                 ┌────────────────┴────────────────┐
                 │ Match?                          │ No Match / Plain Text
                 ▼                                 ▼
         [Binary Format Identified]   [Tier 2: Text Heuristic Engine]
       (Images, Audio, Video, Archives)    Inspects 4-8KB sample using
                                           weighted keywords & regex
                                                   │
                                  ┌────────────────┴────────────────┐
                                  │ Match?                          │ No Match
                                  ▼                                 ▼
                     [Documents & Code Identified]     [Tier 3: Extension Fallback]
                     (Invoices, Resumes, Python, SQL)
```

---

## 💻 Installation

ByteSift requires **Python 3.9+** and has **zero external package dependencies**.

```bash
# Clone the repository
git clone https://github.com/PramudithaN/bytesift.git
cd bytesift

# Run directly
python -m bytesift --help

# Optional: Install as an editable CLI command in your environment
pip install -e .
```

---

## 🎯 Usage

### 1. Interactive Desktop GUI

Launch the native, lightweight GUI:
```bash
python -m bytesift gui
# or if installed:
bytesift gui
```
- Select your target folder.
- Click **"🔍 Preview Scan"** to see what files were detected and where they will go.
- Click **"⚡ Organize Files"** to apply changes.
- Click **"↩️ Undo Last Run"** to restore files back to their exact original locations.

---

### 2. Command Line Interface (CLI)

#### **Scan & Preview (Dry Run)**
Inspects the folder and prints a preview table without moving any files:
```bash
python -m bytesift scan "C:\Users\username\Downloads"
```

#### **Organize Files**
Organizes files with confirmation prompt:
```bash
python -m bytesift organize "C:\Users\username\Downloads"
```

**Options:**
```bash
# Organize without confirmation prompt
python -m bytesift organize "D:\MessyFolder" --yes

# Group images and videos into Year-Month subfolders (e.g., Images/JPEG/2024-05)
python -m bytesift organize "D:\Photos" --group-by-date

# Organize by timeline instead of categories
python -m bytesift organize "D:\Archive" --strategy date

# Include nested subfolders recursively
python -m bytesift organize "D:\MessyFolder" -r

# Disable duplicate detection
python -m bytesift organize "D:\MessyFolder" --no-duplicates
```

#### **Undo / Rollback**
Reverts the last organization session and cleans up empty folders:
```bash
python -m bytesift undo "C:\Users\username\Downloads"
```

---

## 🧪 Testing & Verification

Run the built-in test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Benchmark:
* **8 test suites executed in < 0.05 seconds.**
* Memory footprint: **~22 MB**.

---

## 🛡️ Safety & Integrity Principles

1. **Collision Safe:** If a file with the same name already exists in the destination folder, ByteSift automatically suffixes the file (`filename (1).ext`) to ensure no data is ever overwritten.
2. **Transaction Logging:** Every move operation is journaled to `.bytesift_history.json`.
3. **Ignored Systems:** System directories (`.git`, `node_modules`, `.venv`, `Thumbs.db`, `.DS_Store`) are automatically skipped.

---

## 📄 License

MIT License. Free for personal and commercial use.
