# Box Sender Tool

This tool allows sending emails that appear to originate from Box, with customizable sender names and attachments generated from HTML content.

## Features

- **Interactive Setup**: Run a wizard to configure SMTP, optional IMAP, and DKIM settings.
- **DKIM Signing**: Automatically signs outgoing emails with DKIM to improve authentication and inboxing rates.
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
1.  Generate a DKIM private/public key pair for your domain.
2.  Publish the public key in your domain's DNS records.
3.  Provide the path to your private key file and your DKIM selector during the setup wizard.

Signing your emails with DKIM proves that the email was authorized by the domain owner, which significantly helps in passing spam filters and reaching the inbox.

## Usage

1.  Place your recipient emails in `leads/leads.txt`.
2.  Run `start.bat` (Windows) or `python3 sender.py`.
