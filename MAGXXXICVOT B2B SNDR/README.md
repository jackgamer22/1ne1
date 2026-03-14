# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing.

## Features
- **SMTP Integration**: Sends emails using standard SMTP servers.
- **IMAP Automation**: Automatically locates sent emails and moves them to an Archive folder.
- **HTML Emails**: Supports rich HTML content with embedded logos and signatures.
- **Multi-Contact Sending**: Automates sending to a list of contacts.
- **Error Handling**: Robust (and slightly chaotic) error handling.

## Setup
1. Copy `config.example.json` to `config.json`.
2. Edit `config.json` with your SMTP and IMAP credentials.
3. Add your contacts to the `contacts` list in `config.json`.
4. (Optional) Provide a base64 encoded logo in `logo_base64` and your box signature in `signature`.
5. Ensure you have Python 3 installed.

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Configuration
The `config.json` file contains:
- `smtp`: Connection details for outgoing mail.
- `imap`: Connection details for incoming mail (to move sent items).
- `email`:
    - `contacts`: List of recipient emails.
    - `subject`: The subject line.
    - `body`: Plain text body (will be converted to HTML).
    - `logo_base64`: Base64 string of your logo image.
    - `signature`: Your professional box signature.

## Disclaimer
This project is for educational/fictional purposes.
