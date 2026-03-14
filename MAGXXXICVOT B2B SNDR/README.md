# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, proxy rotation, and high-fidelity HTML attachment conversion.

## Features
- **HTML Attachment Conversion**: Automatically converts `.html` attachments to high-fidelity PDF, PNG, and SVG formats using Playwright. This ensures "all tags are active" and look perfect for the recipient.
- **Attachment Toggles**: Global toggle to enable/disable sending attachments.
- **Auto-Discovery**: Provide just your email and password, and the sender will automatically detect your IMAP and SMTP server settings.
- **Proxy Rotator**: Supports SOCKS5/SOCKS4 proxies with automatic validation via ipify.
- **CLI Toggles**: Toggle proxy usage on/off via command-line flags.
- **Contact Auto-Discovery**: Automatically scans your IMAP INBOX to find leads.
- **Auto-Drafting Invites**: Generates context-aware invite messages (e.g., Google Meet style) based on previous conversations.
- **Real-time Dashboard**: A beautiful tabular display using `rich` to track send status.
- **HTML/Plaintext Toggle**: Easily switch between rich HTML and clean plaintext formats.
- **SMTP/IMAP Automation**: Full lifecycle automation.

## Setup
### Windows
1. Open the project folder.
2. Double-click `setup.bat`. This will install all dependencies (including Playwright and Chromium) and create your `config.json` file.

### Linux/macOS
1. Ensure you have Python 3 installed.
2. Install the required libraries:
   ```bash
   pip install rich PySocks requests defusedxml playwright
   playwright install chromium
   ```
3. Copy `config.example.json` to `config.json`.

## Configuration
Edit `config.json`:
- **HTML Conversion**:
    - `send_attachments`: `true/false` to toggle all attachments.
    - `convert_html_attachments`: `true` to enable HTML processing.
    - `attachment_output_formats`: List of formats (`pdf`, `png`, `svg`).
- **Auto-Discovery**:
    - Set `auto_discovery` to `true` in the `auth` section.

## Usage
Run the sender script:
```bash
python3 sender.py
```

### Command-Line Arguments
- `--use-proxy`: Force enable proxy usage.
- `--no-proxy`: Force disable proxy usage.

## Disclaimer
This project is for educational/fictional purposes.
