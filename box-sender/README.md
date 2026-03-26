# Box Sender Tool

This tool allows sending emails that appear to originate from Box, with customizable sender names and attachments generated from HTML content.

## Features

- **Interactive Setup**: Run a wizard to configure SMTP, IMAP, and email settings.
- **Custom Sender Name**: Set any name to appear in the "From" field.
- **Dynamic Attachments**: Generates PDF and PNG attachments from an HTML template using Playwright.
- **External Templates**: Load the email body and attachment content from separate HTML files (`letter.html` and `attachment.html`).
- **Send Delay**: Configurable delay between sending emails to different recipients.
- **IMAP Synchronization**: Automatically appends sent emails to your IMAP 'Sent' folder, making it look as if they were sent directly from your mailbox.
- **One-Click Scripts**: Includes `setup.bat` and `start.bat` for easy installation and execution on Windows.

## Setup

### Windows
1.  Run `setup.bat` to install all dependencies and browser binaries.

### Linux / macOS
1.  **Clone this repository** (if not already done).
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright browser binaries**:
    ```bash
    playwright install chromium
    ```

## Usage

### Windows
1.  Run `start.bat`. On the first run, it will launch the setup wizard automatically.

### Linux / macOS
Once configured, run the sender script:
```bash
python3 sender.py
```

The script will:
1.  Convert `attachment.html` into a PDF and a PNG image using Playwright.
2.  Connect to the configured SMTP server.
3.  Send an email with `letter.html` as the body and the generated files as attachments to each recipient.
4.  Sync each sent email to the IMAP 'Sent' folder.

## Configuration Options

The tool supports a forced setup wizard at any time:
```bash
python3 sender.py --setup
```

While the setup wizard handles most settings, you can manually edit `config.json`:

-   `smtp_server` / `smtp_port` / `smtp_user` / `smtp_pass`: SMTP credentials.
-   `imap_server` / `imap_port` / `imap_user` / `imap_pass`: IMAP credentials for Sent folder sync.
-   `sender_name`: The name displayed in the "From" field.
-   `sender_email`: The email address displayed in the "From" field.
-   `recipient_emails`: A list of recipient email addresses.
-   `subject`: The email subject.
-   `letter_path`: Path to the HTML file for the email body.
-   `attachment_html_path`: Path to the HTML file for the attachment content.
-   `delay_seconds`: Delay in seconds between each email.
