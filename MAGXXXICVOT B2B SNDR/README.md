# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, proxy rotation, and high-fidelity HTML attachment conversion.

## Features
- **Advanced HTML Conversion**: Converts `.html` files to high-fidelity PDF, PNG, and SVG using Playwright.
- **Auto-Minification**: Optional HTML minification using `htmlmin`.
- **Strict Attachment Management**: Global toggle to enable/disable all attachments.
- **Auto-Discovery**: Automatic IMAP and SMTP server setting detection.
- **Proxy Rotator**: SOCKS5/SOCKS4 rotation with validation.
- **Real-time Dashboard**: Beautiful tabular display of sending status.
- **Personalized Invites**: Context-aware messages based on conversation history.

## Setup
### Windows
1. Open the project folder.
2. Double-click `setup.bat`. This installs all dependencies.

### Linux/macOS
1. Ensure Python 3 is installed.
2. Install libraries:
   ```bash
   pip install rich PySocks requests defusedxml playwright htmlmin
   playwright install chromium
   ```

## Usage
### Windows
- Double-click `start.bat` to begin the automation.

### Linux/macOS
Run the sender script directly:
```bash
python3 sender.py
```

## Configuration
Key `config.json` settings:
- `send_attachments`: `true/false` - Master toggle for attachments.
- `minify_html`: `true/false` - Minify HTML attachments before conversion.
- `convert_html_attachments`: `true/false` - Enable HTML-to-PDF/PNG/SVG conversion.

## Disclaimer
This project is for educational/fictional purposes.
