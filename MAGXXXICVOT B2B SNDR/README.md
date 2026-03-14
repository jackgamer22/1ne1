# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing.

## Features
- **SMTP Integration**: Sends emails using standard SMTP servers.
- **IMAP Automation**: Automatically locates sent emails and moves them to an Archive folder.
- **Error Handling**: Robust (and slightly chaotic) error handling.

## Setup
1. Copy `config.example.json` to `config.json`.
2. Edit `config.json` with your SMTP and IMAP credentials.
3. Ensure you have Python 3 installed.

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Configuration
The `config.json` file contains three main sections:
- `smtp`: Connection details for your outgoing mail server.
- `imap`: Connection details for your incoming mail server (used to move sent mail).
- `email`: The content and recipient of the email you want to send.

## Disclaimer
This project is for educational/fictional purposes.
