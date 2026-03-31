# MagxxicVox Advance Email Sorter

A high-performance, multi-threaded C application designed to sort and verify large lists of email addresses with a beautiful live dashboard.

## Features

- **Beautiful Live Dashboard**: Real-time visualization of processing progress, statistics, and provider breakdown.
- **Cross-Platform Compatibility**: Supports both Linux/macOS (POSIX) and Windows (MinGW-w64).
- **Multi-threaded Processing**: Uses POSIX threads (`pthread`) to parallelize email verification for maximum speed.
- **Advanced Provider Detection**: Extensive list of security providers, regional ISPs, and global hosting platforms.
- **Syntax Validation**: Checks for basic email structure.
- **DNS & SMTP Verification**: Verifies domain records and attempts SMTP reachability (Port 25).
- **Thread Safety**: Uses mutexes to ensure safe concurrent file writes and statistics updates.
- **Signal Handling**: Supports pause/resume/stop on Linux and graceful stop on Windows.

## Compilation & Setup

### Windows (Quick Start)
1. Ensure you have [MinGW-w64](https://www.mingw-w64.org/) installed and in your PATH.
2. Run `setup.bat`. This will compile the project and generate `email_sorter.exe`.

### Linux/macOS
To compile the project, run:
```bash
make
```
This will produce the `email_sorter` executable.

## Usage

Prepare a file named `emails.txt` containing one email address per line.

Run the sorter:
```bash
./email_sorter [input_file] [output_folder]
```

### Defaults:
- `input_file`: `emails.txt`
- `output_folder`: `output`

## Signal Controls (Linux/macOS)

- **Pause**: `kill -USR1 <pid>`
- **Resume**: `kill -USR2 <pid>`
- **Stop**: `kill -INT <pid>` (or `Ctrl+C`)
