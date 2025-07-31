# Node.js Email Marketing Bot

This project is a powerful email marketing agent built with Node.js. It is fully controllable via a Telegram bot, allowing you to configure and launch bulk email campaigns from anywhere.

## Key Features

- **Telegram Bot Control:** Configure every aspect of your email campaign through a simple command interface on Telegram.
- **Dynamic Content:**
    - Use multiple "From" names, "From" emails, and subjects, which are rotated for each email sent.
    - Send a fully custom HTML letter.
- **HTML to PDF Attachments:** Automatically converts an HTML file into a PDF and attaches it to the emails on the fly.
- **Multiple SMTP Support:** Configure multiple SMTP servers for load distribution and rotation.
- **Background Sending:** The email sending process runs in the background, so the bot remains responsive.
- **Status Tracking:** Get real-time status updates on your campaign's progress.

## Prerequisites

- Node.js (v14 or higher)
- npm
- A Telegram Bot Token
- Your Telegram User ID

## 🚀 Setup Instructions

1.  **Clone or Download:**
    Get all the project files onto your server or local machine.

2.  **Install Dependencies:**
    Navigate to the project directory in your terminal and run:
    ```bash
    npm install
    ```
    This will install all the necessary libraries from `package.json`, including `nodemailer`, `puppeteer`, and the Telegram API wrapper.

3.  **Create Environment File:**
    Rename `.env.example` to `.env` and fill in your details:
    ```ini
    # .env
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
    TELEGRAM_USER_ID=YOUR_TELEGRAM_USER_ID_HERE
    ```
    - `TELEGRAM_BOT_TOKEN`: Get this from the "BotFather" on Telegram.
    - `TELEGRAM_USER_ID`: Get your personal user ID from a bot like "@userinfobot".

4.  **Configure SMTP and Content:**
    Open `config.json` and add your SMTP server details and content for rotation.
    ```json
    {
      "smtp_servers": [
        {
          "id": "my_smtp",
          "host": "smtp.example.com",
          "port": 587,
          "secure": false,
          "auth": {
            "user": "user@example.com",
            "pass": "password123"
          }
        }
      ],
      "from_names": ["Support Team", "Marketing"],
      "from_emails": ["noreply@example.com", "contact@example.com"],
      "subjects": ["An Important Update", "A Special Offer for You"]
    }
    ```

5.  **Prepare Initial Files:**
    - **`letter.html`**: Edit this file with the HTML content you want for your email body.
    - **`attachment_source.html`**: Edit this file with the HTML content that will be converted into a PDF attachment.
    - **`contacts.txt`**: Add your recipient email addresses, one per line.

## ▶️ Running the Bot

Once setup is complete, start the bot from your terminal:

```bash
npm start
```
or
```bash
node telegramBot.js
```

The bot will now be running and listening for your commands on Telegram.

## 🤖 Bot Commands

All commands can only be used by the authorized `TELEGRAM_USER_ID`.

### Configuration Commands
- `/start`
  - Displays the welcome message and a list of all available commands.

- `/fromname <Your Name>`
  - Sets a specific "From" name for the campaign, overriding the rotation.
  - Example: `/fromname Acme Inc Support`

- `/frommail <your@email.com>`
  - Sets a specific "From" email, overriding the rotation.
  - Example: `/frommail support@acme.com`

- `/subject <Your Subject>`
  - Sets a specific subject line, overriding the rotation.

- `/selectfrom`
  - Shows an inline keyboard to select a "From" email from the list in `config.json`.

- `/selectsubject`
  - Shows an inline keyboard to select a subject from the list in `config.json`.

### File Management
To use the following commands, you must first **upload a file** directly to the bot.
- `/setletter`
  - Assigns the last uploaded HTML file to be the email body.
- `/setattachment`
  - Assigns the last uploaded HTML file to be the source for the PDF attachment.
- `/setcontacts`
  - Assigns the last uploaded `.txt` file as the new contact list.

### Sending and Status
- `/send`
  - Displays a final preview of the campaign settings (from name/email, subject, file paths, contact count).
  - You must use `/confirm` after this command to start sending.

- `/confirm`
  - After using `/send`, this command starts the email sending process.

- `/status`
  - Checks the progress of a running campaign or shows the results of the last completed one.

- `/cancel`
  - Immediately stops a currently running email campaign.

---
**Note:** This is a powerful tool. Always ensure you are complying with anti-spam laws and have permission to email the contacts on your list.
