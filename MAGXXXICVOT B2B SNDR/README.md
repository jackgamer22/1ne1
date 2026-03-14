# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing and a beautiful real-time dashboard.

## Features
- **Real-time Dashboard**: A beautiful tabular display using `rich` to track send status, recipients, and timing.
- **Auto-Drafting (Contextual)**: Automatically fetches the last conversation subject from IMAP to personalize your emails.
- **HTML/Plaintext Toggle**: Easily switch between rich HTML and clean plaintext formats.
- **Attachments**: Support for PDF, SVG, and Image attachments.
- **Personalized Placeholders**: Use `{{ context }}` in your subject or body to inject conversation-specific data.
- **SMTP Integration**: Sends emails using standard SMTP servers.
- **IMAP Automation**: Automatically locates sent emails and moves them to an Archive folder.

## Setup
1. Copy `config.example.json` to `config.json`.
2. Edit `config.json` with your SMTP and IMAP credentials.
3. Add your contacts to the `contacts` list.
4. Set `use_html` to `true` or `false` as desired.
5. List any file paths in `attachments` you wish to send.
6. Ensure you have Python 3 and the `rich` library installed:
   ```bash
   pip install rich
   ```

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Configuration
The `config.json` file contains:
- `smtp`: Connection details for outgoing mail.
- `imap`: Connection details for incoming mail (to fetch context and move sent items).
- `email`:
    - `contacts`: List of recipient emails.
    - `subject`: Use `{{ context }}` for personalization.
    - `body`: Use `{{ context }}` for personalization.
    - `use_html`: Toggle between HTML and Plaintext.
    - `logo_base64`: Base64 string of your logo image (HTML only).
    - `signature`: Your professional box signature.
    - `attachments`: List of local file paths to attach.

## Disclaimer
This project is for educational/fictional purposes.
