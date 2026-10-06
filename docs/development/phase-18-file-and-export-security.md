# Phase 18 — File & Export Security Architecture

## 1. FileGuard Magic Byte Inspection
`FileGuard` validates real file binary signatures and blocks dangerous executable binaries:
- Windows PE executables (`MZ` header)
- Linux ELF binaries (`\x7fELF`)
- Shell scripts (`#!/`)
- Embedded HTML/JS scripts (`<script`, `<!DOCTYPE html`)

## 2. Path Traversal & Zip Bomb Defenses
- All uploaded filenames are stripped of null bytes (`\x00`), path separators (`/`, `\`), and directory traversal sequences (`..`).
- Compressed archives (`.zip`, `.docx`, `.xlsx`) are inspected for path traversal entries and compression ratios exceeding 100x or 150MB uncompressed size.

## 3. Spreadsheet Formula Injection Neutralization
`ExportGuard` prepends a single quote (`'`) to any exported tabular cell starting with `=`, `+`, `-`, `@`, `\t`, `\r`, `|`, or `%`, preventing Dynamic Data Exchange (DDE) and code execution in Microsoft Excel, LibreOffice, and Google Sheets.
