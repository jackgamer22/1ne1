const nodemailer = require('nodemailer');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// --- Configuration ---
const CONFIG_FILE = 'config.json';
const SETTINGS_FILE = 'settings.json'; // Written by the bot
const CONTACTS_FILE = 'contacts.txt';
const STATUS_FILE = 'sending_status.json';
const OPEN_LOG_FILE = 'open_log.txt'; // For simplicity, though a DB is better for opens
const PDF_OUTPUT_PATH = path.join(__dirname, 'attachment.pdf');

// --- Helper Functions ---

/**
 * Delays execution for a given number of milliseconds.
 * @param {number} ms - The number of milliseconds to wait.
 */
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Logs a message to both the console and a status file.
 * @param {string} message - The message to log.
 * @param {object} status - The current status object.
 */
function updateStatus(message, status) {
    console.log(message);
    status.last_message = message;
    fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2));
}

/**
 * Creates a PDF from an HTML file using Puppeteer.
 * @param {string} htmlFilePath - The path to the source HTML file.
 * @returns {Promise<string>} The path to the generated PDF.
 */
async function createPdfFromHtml(htmlFilePath) {
    if (!fs.existsSync(htmlFilePath)) {
        throw new Error(`HTML file for PDF conversion not found: ${htmlFilePath}`);
    }
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
    await page.pdf({
        path: PDF_OUTPUT_PATH,
        format: 'A4',
        printBackground: true
    });
    await browser.close();
    return PDF_OUTPUT_PATH;
}


// --- Main Sending Logic ---

async function sendBulkEmails() {
    // 1. Load all configurations and settings
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    const settings = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
    const contacts = fs.readFileSync(CONTACTS_FILE, 'utf8')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && line.includes('@'));

    if (contacts.length === 0) {
        console.log("No contacts found. Exiting.");
        return;
    }

    const status = {
        total: contacts.length,
        sent: 0,
        success: 0,
        failed: 0,
        start_time: new Date().toISOString(),
        end_time: null,
        last_message: 'Starting...'
    };
    updateStatus('Email sending process initiated.', status);

    try {
        // 2. Prepare letter and attachment
        updateStatus('Preparing letter and attachment...', status);
        const letterHtml = fs.readFileSync(settings.letter_file, 'utf8');
        let attachmentPath = null;
        if (settings.attachment_file && fs.existsSync(settings.attachment_file)) {
            updateStatus(`Converting ${settings.attachment_file} to PDF...`, status);
            attachmentPath = await createPdfFromHtml(settings.attachment_file);
            updateStatus(`PDF attachment created at ${attachmentPath}`, status);
        }

        // 3. Loop through contacts and send emails
        for (const contact of contacts) {
            try {
                // Rotate through SMTP servers, from names, and subjects
                const smtpConfig = config.smtp_servers[status.sent % config.smtp_servers.length];
                const fromName = settings.from_name || config.from_names[status.sent % config.from_names.length];
                const fromEmail = settings.from_email || config.from_emails[status.sent % config.from_emails.length];
                const subject = settings.subject || config.subjects[status.sent % config.subjects.length];

                const transport = nodemailer.createTransport(smtpConfig);

                const mailOptions = {
                    from: `"${fromName}" <${fromEmail}>`,
                    to: contact,
                    subject: subject,
                    html: letterHtml,
                };

                if (attachmentPath) {
                    mailOptions.attachments = [{
                        filename: 'attachment.pdf',
                        path: attachmentPath,
                        contentType: 'application/pdf'
                    }];
                }

                await transport.sendMail(mailOptions);
                status.success++;
                updateStatus(`Successfully sent to ${contact} via ${smtpConfig.id}`, status);

            } catch (error) {
                status.failed++;
                updateStatus(`Failed to send to ${contact}: ${error.message}`, status);
            } finally {
                status.sent++;
                // Add a random delay to be less robotic
                const randomDelay = Math.floor(Math.random() * (5000 - 1000 + 1) + 1000); // 1-5 seconds
                await delay(randomDelay);
            }
        }

    } catch (error) {
        updateStatus(`A critical error occurred: ${error.message}`, status);
    } finally {
        // 4. Cleanup and final status update
        if (fs.existsSync(PDF_OUTPUT_PATH)) {
            fs.unlinkSync(PDF_OUTPUT_PATH); // Delete the temporary PDF
        }
        status.end_time = new Date().toISOString();
        updateStatus(`Process finished. Success: ${status.success}, Failed: ${status.failed}.`, status);
        console.log("Email sending process complete.");
    }
}

// Execute the function when the script is run
sendBulkEmails();
