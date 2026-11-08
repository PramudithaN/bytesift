# ByteSift

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-20232A?style=for-the-badge&logo=python&logoColor=white)
![CLI](https://img.shields.io/badge/CLI-4EAA25?style=for-the-badge&logo=gnubash&logoColor=white)
![Version](https://img.shields.io/badge/Version-0.1.0-007ACC?style=for-the-badge)

ByteSift is a lightweight, offline file classification and organization utility designed to inspect file contents directly rather than relying solely on file extensions. Operating without artificial intelligence, external network connectivity, or third-party dependencies, it provides deterministic, low-latency categorization and deduplication.

---

## Overview

Traditional file organizers depend heavily on file extensions, failing when extensions are incorrect, missing, or generic. ByteSift addresses this through a multi-tiered inspection pipeline:

1. **Binary Magic Bytes:** Analyzes initial byte sequences to determine actual container and binary formats (e.g., PDF, JPEG, PNG, ZIP, Office OpenXML, executables).
2. **Text Content Heuristics:** Evaluates bounded text samples (4-8 KB) against weighted keyword and structural patterns to identify invoices, resumes, contracts, source code, and system logs.
3. **Metadata & Timestamp Parsing:** Extracts embedded timestamps (such as JPEG EXIF markers) to enable chronological archiving.
4. **Content Deduplication:** Employs size-grouped SHA-256 hashing to identify identical files without unnecessary read cycles.

---

## Key Features

- **Offline and Private:** Executes entirely within local memory. No network requests, telemetry, or external models are used.
- **Content-Driven Classification:** Reliably detects file formats regardless of file extension accuracy.
- **Deterministic Heuristic Engine:** Classifies unstructured text and documents through pattern matching rather than statistical language models.
- **Duplicate Isolation:** Automatically routes identical files into a designated duplicates directory.
- **Collision Protection:** Automatically applies numerical suffixes (`filename (1).ext`) to prevent overwriting existing files.
- **Reversible Operations:** Records each file relocation in a local transaction log (`.bytesift_history.json`), allowing full rollbacks.
- **Zero External Dependencies:** Built using the standard library, ensuring low memory consumption (< 30 MB) and rapid startup times.
- **Dual Interface:** Provides both a command-line interface (CLI) and a native modern Windows Fluent interface with automatic system Dark/Light mode detection.

---

## Architecture

```
                    +--------------------+
                    |     Input File     |
                    +---------+----------+
                              |
                              v
                [Tier 1: Magic Byte Inspection]
          Reads initial 16-64 bytes for file signatures
                              |
             +----------------+----------------+
             | Binary Match                    | No Match / Text
             v                                 v
   [Format Identified]           [Tier 2: Text Heuristic Engine]
 (Images, Audio, Archives)        Scans 4-8 KB for keywords/regex
                                               |
                              +----------------+----------------+
                              | Text Match                      | Unmatched
                              v                                 v
                     [Document/Code Type]             [Tier 3: Extension Fallback]
```

---

## Requirements and Installation

- **Python:** Version 3.9 or higher.
- **Dependencies:** None (standard library only).

### Installation

Clone the repository and run directly:

```bash
git clone https://github.com/PramudithaN/bytesift.git
cd bytesift
```

To install the executable script into your active Python environment:

```bash
pip install -e .
```

---

## Usage

### 1. Graphical Interface

To launch the desktop interface:

```bash
python -m bytesift.cli gui
```

The GUI allows directory selection, preview of categorization plans, execution, and rollback of previous actions.

---

### 2. Command Line Interface

#### Preview Organization Plan (Dry Run)

Scans the target directory and outputs planned operations without moving files:

```bash
python -m bytesift.cli scan "/path/to/directory"
```

#### Execute Organization

Analyzes contents and moves files into categorized subdirectories:

```bash
python -m bytesift.cli organize "/path/to/directory"
```

**Options:**

- `--yes`: Skips the interactive confirmation prompt.
- `--strategy [smart|date|type]`: Selects classification mode (default: `smart`).
- `--group-by-date`: Appends `YYYY-MM` subfolders for media assets.
- `--no-duplicates`: Disables duplicate detection.
- `-r, --recursive`: Processes subdirectories recursively.
- `--dry-run`: Runs full analysis without altering the file system.

#### Undo Previous Operation

Restores all files from the latest session to their original paths and cleans up empty directories:

```bash
python -m bytesift.cli undo "/path/to/directory"
```

---

## Verification and Testing

Execute the unit test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The test suite covers:

- Binary magic byte validation across common formats.
- Text heuristic detection across structured documents and code.
- End-to-end plan generation, collision resolution, and transaction rollbacks.

---

## Safety and Rollback Mechanism

1. **Transaction Journaling:** A session record is committed to `.bytesift_history.json` upon completion of file moves.
2. **Safe Rollback:** The `undo` command reverses moves in inverse order, restoring original file locations.
3. **Excluded Directories:** Hidden directories and standard version control/dependency folders (`.git`, `node_modules`, `.venv`) are ignored by default.

---

## License

This project is licensed under the MIT License.
