# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, and proxy rotation.

## Features
- **Auto-Discovery**: Provide just your email and password, and the sender will automatically detect your IMAP and SMTP server settings using Thunderbird's autoconfig service.
- **Proxy Rotator**: Supports SOCKS5/SOCKS4 proxies with automatic validation via ipify. Hides your local IP from mail servers.
- **CLI Toggles**: Toggle proxy usage on/off via command-line flags.
- **Contact Auto-Discovery**: Automatically scans your IMAP INBOX to find people you've recently conversed with.
- **Auto-Drafting Invites**: Generates "convincing" invite messages based on the context of your previous conversation.
- **Real-time Dashboard**: A beautiful tabular display using `rich` to track send status and recipients.
- **HTML/Plaintext Toggle**: Easily switch between rich HTML and clean plaintext formats.
- **Attachments**: Support for PDF, SVG, and Image attachments.
- **SMTP/IMAP Automation**: Full lifecycle automation from discovery to archiving sent mail.

## Setup
### Windows
1. Open the project folder.
2. Double-click `setup.bat`. This will install all dependencies and create your `config.json` file.

### Linux/macOS
1. Ensure you have Python 3 installed.
2. Install the required libraries:
   ```bash
   pip install rich PySocks requests defusedxml
   ```
3. Copy `config.example.json` to `config.json`.

## Configuration
Edit `config.json`:
- **Option A (Easy)**: Just fill in the `auth` section with your email and password, and set `auto_discovery` to `true`.
- **Option B (Manual)**: Provide full `smtp` and `imap` server details.
- **Toggles**:
    - `auto_discover_contacts`: Set to `true` to find new leads in your inbox.
    - `auto_draft_invite`: Set to `true` to use the `invite_template`.

## Usage
Run the sender script:
```bash
python3 sender.py
```

### Command-Line Arguments
- `--use-proxy`: Force enable proxy usage, overriding `config.json`.
- `--no-proxy`: Force disable proxy usage, overriding `config.json`.

## Disclaimer
This project is for educational/fictional purposes.
