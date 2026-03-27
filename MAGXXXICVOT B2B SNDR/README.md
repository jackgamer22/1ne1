# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, proxy rotation, DKIM signing, and high-fidelity HTML attachment conversion.

## Features
- **Interactive Configuration**: A beautiful CLI wizard to set up credentials, toggles, and server settings.
- **DKIM Signing**: Support for signing outgoing emails with your domain keys for better deliverability.
- **Auto-Discovery**: Automatic IMAP and SMTP server detection.
- **Proxy Rotator**: SOCKS5/SOCKS4 rotation with validation.
- **Advanced HTML Conversion**: Converts `.html` files to high-fidelity PDF, PNG, and SVG using Playwright.
- **Auto-Minification**: Optional HTML minification using `htmlmin`.
- **Real-time Dashboard**: Beautiful tabular display of sending status.

## Setup
### Windows
1. Open the project folder.
2. Double-click `setup.bat`. This installs all dependencies.

### Linux/macOS
1. Ensure Python 3 is installed.
2. Install libraries:
   ```bash
   pip install rich PySocks requests defusedxml playwright htmlmin dkimpy
   playwright install chromium
   ```

## Usage
### Windows
- Double-click `start.bat` or run `python sender.py`.

### First Run
The script will guide you through an interactive setup if `config.json` is missing. Use the `--setup` flag anytime to reconfigure.

## Configuration
Key settings managed via Dashboard/`config.json`:
- `dkim`: Enable signing, set your domain, selector, and path to your private key file.
- `automated_mode`: Toggle between fully automated or manual confirmation per recipient.
- `send_attachments`: Master toggle for attachments.

## Disclaimer
This project is for educational/fictional purposes.
