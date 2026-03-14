# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, proxy rotation, and high-fidelity HTML attachment conversion.

## Features
- **Advanced HTML Conversion**: Converts `.html` files to high-fidelity PDF, PNG, and SVG using Playwright with optimized stability flags.
- **Auto-Minification**: Optional HTML minification using `htmlmin` to reduce attachment size and improve delivery reliability.
- **Strict Attachment Management**: Global toggle to completely enable or disable all attachment processing.
- **Auto-Discovery**: Automatic IMAP and SMTP server setting detection.
- **Proxy Rotator**: SOCKS5/SOCKS4 rotation with validation.
- **Real-time Dashboard**: Beautiful tabular display of sending status.
- **Personalized Invites**: Context-aware messages based on conversation history.

## Setup
### Windows
1. Open the project folder.
2. Double-click `setup.bat`. This installs all dependencies (Playwright, htmlmin, etc.).

### Linux/macOS
1. Ensure Python 3 is installed.
2. Install libraries:
   ```bash
   pip install rich PySocks requests defusedxml playwright htmlmin
   playwright install chromium
   ```

## Configuration
Key `config.json` settings:
- `send_attachments`: `true/false` - Master toggle for attachments.
- `minify_html`: `true/false` - Minify HTML attachments before conversion.
- `convert_html_attachments`: `true/false` - Enable HTML-to-PDF/PNG/SVG conversion.

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Disclaimer
This project is for educational/fictional purposes.
