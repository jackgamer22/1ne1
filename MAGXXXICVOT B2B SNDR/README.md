# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, AI-inspired auto-drafting, and proxy rotation.

## Features
- **Proxy Rotator**: Supports SOCKS5/SOCKS4 proxies with automatic validation via ipify. Hides your local IP from mail servers.
- **Contact Auto-Discovery**: Automatically scans your IMAP INBOX to find people you've recently conversed with.
- **Auto-Drafting Invites**: Generates "convincing" invite messages based on the context of your previous conversation.
- **Real-time Dashboard**: A beautiful tabular display using `rich` to track send status and recipients.
- **HTML/Plaintext Toggle**: Easily switch between rich HTML and clean plaintext formats.
- **Attachments**: Support for PDF, SVG, and Image attachments.
- **SMTP/IMAP Automation**: Full lifecycle automation from discovery to archiving sent mail.

## Setup
1. Copy `config.example.json` to `config.json`.
2. Edit `config.json` with your SMTP and IMAP credentials.
3. Proxy Configuration:
   - Set `use_proxy` to `true`.
   - Add your SOCKS5 proxies to the `proxies` list in `socks5://user:pass@host:port` format.
4. Toggles:
   - Set `auto_discover_contacts` to `true` to find new leads.
   - Set `auto_draft_invite` to `true` to use the `invite_template`.
5. Ensure you have Python 3 and the required libraries:
   ```bash
   pip install rich PySocks requests
   ```

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Configuration
Key `config.json` sections:
- `proxy`: Manage your proxy list and toggle.
- `email`:
    - `auto_discover_contacts`: Enable lead finding.
    - `auto_draft_invite`: Enable contextual invite drafting.
    - `invite_template`: Template for the personalized invitation.

## Disclaimer
This project is for educational/fictional purposes.
