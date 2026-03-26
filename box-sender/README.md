# Box Sender Tool

This tool allows sending emails that appear to originate from Box, with customizable sender names and attachments generated from HTML content.

## Features

- **Interactive Setup**: Run a wizard to configure SMTP, IMAP, and email settings.
- **Smart Delivery Headers**: Automatically adds `Message-ID`, `X-Mailer`, `Date`, and high-priority headers to improve delivery.
- **Leads Management**: Load recipient emails from a simple text file in the `leads/` folder.
- **Personalization Tags**: Use tags like `[-email-]`, `[-sender_name-]`, and `[-sender_email-]` in your subject, body, and attachments.
- **Optional Attachments**: Choose whether to send attachments and select your preferred format (PDF, PNG, or SVG).
- **HTML Minification**: Automatically minifies HTML content for attachments using `minify-html` to reduce size and improve rendering.
- **Dynamic Attachments**: Generates per-recipient personalized attachments using Playwright.
- **Send Delay**: Configurable delay between sending emails.
- **IMAP Synchronization**: Automatically appends sent emails to your IMAP 'Sent' folder.
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

## Usage

### Windows
1.  Place your recipient emails in `leads/leads.txt`.
2.  Run `start.bat`.

### Linux / macOS
1.  Place your recipient emails in `leads/leads.txt`.
2.  Run the sender script:
    ```bash
    python3 sender.py
    ```

## Personalization Tags

The following tags are supported in `subject`, `letter.html`, and `attachment.html`:
- `[-email-]`: The recipient's email address.
- `[-sender_name-]`: The sender name from configuration.
- `[-sender_email-]`: The sender email from configuration.
