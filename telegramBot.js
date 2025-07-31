require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');

// --- Basic Configuration ---
const token = process.env.TELEGRAM_BOT_TOKEN;
const ownerId = parseInt(process.env.TELEGRAM_USER_ID, 10);

if (!token || !ownerId) {
    console.error("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID must be set in .env file.");
    process.exit(1);
}

const bot = new TelegramBot(token, { polling: true });

const SETTINGS_FILE = 'settings.json';
const CONTACTS_FILE = 'contacts.txt';
const CONFIG_FILE = 'config.json';
const STATUS_FILE = 'sending_status.json';
const UPLOAD_DIR = path.join(__dirname, 'uploads');

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR);
}

// --- State and Settings Management ---
let settings = {
    from_name: '',
    from_email: '',
    subject: '',
    letter_file: 'letter.html',
    attachment_file: 'attachment_source.html'
};

if (fs.existsSync(SETTINGS_FILE)) {
    settings = JSON.parse(fs.readFileSync(SETTINGS_FILE));
} else {
    fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2));
}

function saveSettings() {
    fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2));
}

let childProcess = null; // To keep track of the sending process

// --- Authorization Middleware ---
const authorized = (handler) => (msg, match) => {
    if (msg.from.id !== ownerId) {
        return bot.sendMessage(msg.chat.id, "Sorry, you are not authorized to use this bot.");
    }
    handler(msg, match);
};

// --- Helper Functions ---
function getContactsCount() {
    if (!fs.existsSync(CONTACTS_FILE)) return 0;
    return fs.readFileSync(CONTACTS_FILE, 'utf8')
        .split('\n')
        .filter(line => line.trim().includes('@')).length;
}


// --- Command Handlers ---

bot.onText(/\/start/, authorized((msg) => {
    const helpText = `
✅ **Email Bot Ready** ✅

**Configuration Commands:**
- \`/fromname <Your Name>\` - Set a specific 'From' name.
- \`/frommail <your@email.com>\` - Set a specific 'From' email.
- \`/subject <Your Subject>\` - Set a specific subject line.
- \`/selectfrom\` - Choose a 'From' email from config.
- \`/selectsubject\` - Choose a subject from config.

**File Commands:**
1. Upload a file (.html, .txt).
2. Use one of these commands to assign it:
   - \`/setletter\` - Assigns the last uploaded file as the HTML letter.
   - \`/setattachment\` - Assigns the last uploaded file as the HTML source for the PDF attachment.
   - \`/setcontacts\` - Assigns the last uploaded .txt file as the contact list.

**Action Commands:**
- \`/send\` - Show a preview of the campaign and prepare to send.
- \`/confirm\` - (Only after /send) Starts the email campaign.
- \`/status\` - Check the progress of the current campaign.
- \`/cancel\` - Stop a running campaign.
    `;
    bot.sendMessage(msg.chat.id, helpText, { parse_mode: 'Markdown' });
}));

// Configuration commands
bot.onText(/\/fromname (.+)/, authorized((msg, match) => {
    settings.from_name = match[1];
    saveSettings();
    bot.sendMessage(msg.chat.id, `📛 From Name set to: *${settings.from_name}*`, { parse_mode: 'Markdown' });
}));

bot.onText(/\/frommail (.+)/, authorized((msg, match) => {
    settings.from_email = match[1];
    saveSettings();
    bot.sendMessage(msg.chat.id, `📧 From Email set to: *${settings.from_email}*`, { parse_mode: 'Markdown' });
}));

bot.onText(/\/subject (.+)/, authorized((msg, match) => {
    settings.subject = match[1];
    saveSettings();
    bot.sendMessage(msg.chat.id, `✉️ Subject set to: *${settings.subject}*`, { parse_mode: 'Markdown' });
}));

// Selection commands
bot.onText(/\/selectfrom/, authorized((msg) => {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    const keyboard = config.from_emails.map(email => ([{ text: email, callback_data: `from_${email}` }]));
    bot.sendMessage(msg.chat.id, '👇 Choose a "From" email:', {
        reply_markup: { inline_keyboard: keyboard }
    });
}));

bot.onText(/\/selectsubject/, authorized((msg) => {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    const keyboard = config.subjects.map(subj => ([{ text: subj.substring(0, 30), callback_data: `subj_${subj}` }]));
    bot.sendMessage(msg.chat.id, '👇 Choose a subject:', {
        reply_markup: { inline_keyboard: keyboard }
    });
}));

// File assignment commands
let lastUploadedFile = {};
bot.onText(/\/setletter/, authorized((msg) => {
    if (lastUploadedFile[msg.chat.id]) {
        settings.letter_file = lastUploadedFile[msg.chat.id];
        saveSettings();
        bot.sendMessage(msg.chat.id, `📄 Letter template set to: *${path.basename(settings.letter_file)}*`, { parse_mode: 'Markdown' });
    } else {
        bot.sendMessage(msg.chat.id, "Please upload an HTML file first.");
    }
}));

bot.onText(/\/setattachment/, authorized((msg) => {
    if (lastUploadedFile[msg.chat.id]) {
        settings.attachment_file = lastUploadedFile[msg.chat.id];
        saveSettings();
        bot.sendMessage(msg.chat.id, `📎 Attachment source set to: *${path.basename(settings.attachment_file)}*`, { parse_mode: 'Markdown' });
    } else {
        bot.sendMessage(msg.chat.id, "Please upload an HTML file first.");
    }
}));

bot.onText(/\/setcontacts/, authorized((msg) => {
    if (lastUploadedFile[msg.chat.id] && lastUploadedFile[msg.chat.id].endsWith('.txt')) {
        fs.copyFileSync(lastUploadedFile[msg.chat.id], CONTACTS_FILE);
        bot.sendMessage(msg.chat.id, `👥 Contacts list updated from *${path.basename(lastUploadedFile[msg.chat.id])}*`, { parse_mode: 'Markdown' });
    } else {
        bot.sendMessage(msg.chat.id, "Please upload a .txt file first.");
    }
}));


// --- Action Commands ---

bot.onText(/\/status/, authorized((msg) => {
    if (childProcess) {
        if (fs.existsSync(STATUS_FILE)) {
            const status = JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
            bot.sendMessage(msg.chat.id, `*Running...*\n${status.sent}/${status.total} - ${status.last_message}`, { parse_mode: 'Markdown' });
        } else {
            bot.sendMessage(msg.chat.id, "Sending process is active, but status file not yet created.");
        }
    } else {
        if (fs.existsSync(STATUS_FILE)) {
            const status = JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
            const finishTime = new Date(status.end_time).toLocaleString();
            bot.sendMessage(msg.chat.id, `*Finished at ${finishTime}*\nSuccess: ${status.success}, Failed: ${status.failed}`, { parse_mode: 'Markdown' });
        } else {
            bot.sendMessage(msg.chat.id, "No active or recent sending process found.");
        }
    }
}));

bot.onText(/\/cancel/, authorized((msg) => {
    if (childProcess) {
        childProcess.kill();
        childProcess = null;
        bot.sendMessage(msg.chat.id, "🛑 Sending process has been cancelled.");
    } else {
        bot.sendMessage(msg.chat.id, "No sending process is currently running.");
    }
}));

let awaitingConfirmation = {};
bot.onText(/\/send/, authorized((msg) => {
    if (childProcess) {
        return bot.sendMessage(msg.chat.id, "A sending process is already running. Use /status to check or /cancel to stop it.");
    }
    const count = getContactsCount();
    const preview = `
*📋 Email Preview:*
- From Name: \`${settings.from_name || 'Rotate from config'}\`
- From Email: \`${settings.from_email || 'Rotate from config'}\`
- Subject: \`${settings.subject || 'Rotate from config'}\`
- Letter: \`${path.basename(settings.letter_file)}\`
- Attachment: \`${path.basename(settings.attachment_file)}\`
- Contacts: \`${count} emails\`

⚠️ Reply \`/confirm\` to begin sending.
    `.trim();
    bot.sendMessage(msg.chat.id, preview, { parse_mode: 'Markdown' });
    awaitingConfirmation[msg.chat.id] = true;
}));

bot.onText(/\/confirm/, authorized((msg) => {
    if (!awaitingConfirmation[msg.chat.id]) {
        return bot.sendMessage(msg.chat.id, "Please use /send first to see the preview.");
    }
    if (childProcess) {
        return bot.sendMessage(msg.chat.id, "A sending process is already running.");
    }

    awaitingConfirmation[msg.chat.id] = false;
    bot.sendMessage(msg.chat.id, "🚀 Forking sender process... Sending will begin shortly.");

    childProcess = fork(path.join(__dirname, 'emailSender.js'));

    childProcess.on('exit', (code) => {
        bot.sendMessage(msg.chat.id, `✅ Sending process finished with code ${code}.`);
        childProcess = null;
    });

    childProcess.on('error', (err) => {
        bot.sendMessage(msg.chat.id, `❌ Sending process encountered a critical error: ${err.message}`);
        childProcess = null;
    });
}));


// --- Callback Query Handler (for inline buttons) ---

bot.on('callback_query', (query) => {
    const { data, message } = query;
    const chatId = message.chat.id;

    if (data.startsWith('from_')) {
        settings.from_email = data.substring(5);
        saveSettings();
        bot.editMessageText(`📧 From Email set to: *${settings.from_email}*`, {
            chat_id: chatId,
            message_id: message.message_id,
            parse_mode: 'Markdown'
        });
    } else if (data.startsWith('subj_')) {
        settings.subject = data.substring(5);
        saveSettings();
        bot.editMessageText(`✉️ Subject set to: *${settings.subject}*`, {
            chat_id: chatId,
            message_id: message.message_id,
            parse_mode: 'Markdown'
        });
    }
});


// --- File Upload Handler ---

bot.on('document', authorized(async (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, "Downloading file...");

    try {
        const filePath = await bot.downloadFile(msg.document.file_id, UPLOAD_DIR);
        lastUploadedFile[chatId] = filePath;
        bot.sendMessage(chatId, `📁 Uploaded: *${path.basename(filePath)}*\n\nUse \`/setletter\`, \`/setattachment\`, or \`/setcontacts\` to assign it.`, { parse_mode: 'Markdown' });
    } catch (error) {
        console.error("File download error:", error);
        bot.sendMessage(chatId, "❌ Failed to download the file.");
    }
}));


console.log("Telegram Bot is running...");
