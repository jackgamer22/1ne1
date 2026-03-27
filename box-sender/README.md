# Box Sender Tool

This tool allows sending emails that appear to originate from Box, with customizable sender names and attachments generated from HTML content.

## Features

- **Interactive Setup**: Run a wizard to configure SMTP, optional IMAP, and DKIM settings.
- **DKIM Signing & Key Generation**: Automatically sign outgoing emails with DKIM. The setup wizard can generate a new RSA-2048 key pair for you and provide DNS TXT record instructions.
- **Advanced Dashboard**: Real-time terminal dashboard showing detailed statistics (Total, Sent, Failed, Synced) and a live status log.
- **Smart Delivery Headers**: Automatically adds `Message-ID`, `X-Mailer`, `Date`, and high-priority headers.
- **Leads Management**: Load recipient emails from a simple text file in the `leads/` folder.
- **Personalization Tags**: Use tags like `[-email-]`, `[-sender_name-]`, and `[-sender_email-]` in your subject, body, and attachments.
- **Optional Attachments**: Choose whether to send attachments and select your preferred format (PDF or PNG).
- **HTML Minification**: Automatically minifies HTML content for attachments using `minify-html`.
- **Dynamic Attachments**: Generates per-recipient personalized attachments using Playwright.
- **One-Click Scripts**: Includes `setup.bat` and `start.bat` for Windows.

## Setup

### Windows
1.  Run `setup.bat` to install all dependencies.

### Linux / macOS
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Install Playwright browser binaries**:
    ```bash
    playwright install chromium
    ```

## DKIM Signing

To use DKIM signing:
1.  Run the setup wizard (`python3 sender.py --setup`).
2.  Choose to "Generate new DKIM keys" when prompted.
3.  The tool will save `dkim_private.key` and display a TXT record.
4.  Publish the provided public key in your domain's DNS records.

Signing your emails with DKIM proves that the email was authorized by the domain owner, which significantly helps in passing spam filters and reaching the inbox.

## Usage

1.  Place your recipient emails in `leads/leads.txt`.
2.  Run `start.bat` (Windows) or `python3 sender.py`.
