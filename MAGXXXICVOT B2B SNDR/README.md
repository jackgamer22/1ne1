# MAGXXXICVOT B2B SNDR

An advanced SMTP mailing utility with automated IMAP post-processing, contact discovery, and AI-inspired auto-drafting.

## Features
- **Contact Auto-Discovery**: Automatically scans your IMAP INBOX to find people you've recently conversed with.
- **Auto-Drafting Invites**: Generates "convincing" invite messages based on the context of your previous conversation.
- **Contextual Personalization**: Cleans conversation subjects (removing Re:/Fwd:) and injects them into templates via `{{ context }}`.
- **Real-time Dashboard**: A beautiful tabular display using `rich` to track send status and recipients.
- **HTML/Plaintext Toggle**: Easily switch between rich HTML and clean plaintext formats.
- **Attachments**: Support for PDF, SVG, and Image attachments.
- **SMTP/IMAP Automation**: Full lifecycle automation from discovery to archiving sent mail.

## Setup
1. Copy `config.example.json` to `config.json`.
2. Edit `config.json` with your SMTP and IMAP credentials.
3. Toggles:
   - Set `auto_discover_contacts` to `true` to find new leads in your inbox.
   - Set `auto_draft_invite` to `true` to use the `invite_template` for personalized invites.
4. Customize your `invite_template` using `{{ context }}`.
5. Ensure you have Python 3 and the `rich` library installed:
   ```bash
   pip install rich
   ```

## Usage
Run the sender script:
```bash
python3 sender.py
```

## Configuration
Key `config.json` fields:
- `auto_discover_contacts`: Enable/disable automatic lead finding.
- `auto_draft_invite`: Enable/disable contextual invite drafting.
- `invite_template`: Template for the personalized invitation.
- `contacts`: Manual list of recipient emails (merged with discovered ones).

## Disclaimer
This project is for educational/fictional purposes.
