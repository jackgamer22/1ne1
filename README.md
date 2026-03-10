# SMTP Mailer Utility

A modular Node.js utility for testing SMTP configurations and sending emails through multiple relays with SOCKS5 proxy support.

## Features

- **Multiple SMTP Support**: Rotate through a list of SMTP servers.
- **SOCKS5 Proxy Support**: Validates and rotates through proxies for each email.
- **Real-time Dashboard**: Monitor success and failure rates in the terminal.
- **Customizable**: External configuration for message templates, recipient lists, and headers.
- **Dry Run Mode**: Test your setup without actually sending emails.

## Setup

1.  **Install Dependencies**:
    ```bash
    npm install
    ```
    (Or run `setup.bat` on Windows).

2.  **Configuration**:
    - Copy `sender-app/config.example.json` to `sender-app/config.json`.
    - Fill in your SMTP details, mailing list, and message content.

## Usage

Start the mailer:
```bash
npm start
```
(Or run `start.bat` on Windows).

To run in dry-run mode (no emails sent, no delays):
```bash
npm start -- --dry-run
```

## Disclaimer

This tool is for educational and authorized testing purposes only. The authors are not responsible for any misuse or damage caused by this software. Always ensure you have permission before sending emails through any service or to any recipient.
