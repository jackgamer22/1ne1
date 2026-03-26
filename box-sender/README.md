# Box Sender Tool

This tool allows sending emails that appear to originate from Box, with customizable sender names and attachments generated from HTML content.

## Setup

1.  **Clone this repository** (if not already done).
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright browser binaries**:
    ```bash
    playwright install chromium
    ```
4.  **Configure the sender**:
    Copy `config.json.example` to `config.json` and fill in your SMTP details and email content.
    ```bash
    cp config.json.example config.json
    ```

## Usage

Run the sender script:
```bash
python3 sender.py
```

The script will:
1.  Convert the `html_content` defined in `config.json` into a PDF and a PNG image using Playwright.
2.  Connect to the configured SMTP server.
3.  Send an email to the list of recipients with the generated files as attachments.

## Configuration Options

-   `smtp_server`: Your SMTP server hostname.
-   `smtp_port`: Your SMTP server port (usually 587 for TLS).
-   `smtp_user`: Your SMTP username.
-   `smtp_pass`: Your SMTP password.
-   `sender_name`: The name displayed in the "From" field.
-   `sender_email`: The email address displayed in the "From" field.
-   `recipient_emails`: A list of recipient email addresses.
-   `subject`: The email subject.
-   `body`: The plaintext body of the email.
-   `html_content`: The HTML content to be converted into PDF and Image attachments.
