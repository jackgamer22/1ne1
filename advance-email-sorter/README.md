# Advance Email Sorter

A high-performance, multi-threaded C application designed to sort and verify large lists of email addresses.

## Features

- **Multi-threaded Processing**: Uses POSIX threads (`pthread`) to parallelize email verification for maximum speed.
- **Syntax Validation**: Checks for basic email structure.
- **DNS Verification**: Verifies if the domain has valid DNS records.
- **SMTP Verification**: Attempts a connection to the mail server's SMTP port (25) to check reachability.
- **Provider Detection**: Automatically categorizes emails by major providers (Gmail, Office365, Yahoo, etc.) based on domain analysis.
- **Thread Safety**: Uses mutexes to ensure safe concurrent file writes and counter updates.
- **Signal Handling**: Supports pause (`SIGUSR1`), resume (`SIGUSR2`), and graceful stop (`SIGINT`).

## Compilation

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

Defaults:
- `input_file`: `emails.txt`
- `output_folder`: `output`

## Signal Controls

- **Pause**: `kill -USR1 <pid>`
- **Resume**: `kill -USR2 <pid>`
- **Stop**: `kill -INT <pid>` (or `Ctrl+C`)
