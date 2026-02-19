const nodemailer = require('nodemailer');
const logger = require('./logger');

async function sendEmail({ ceoCfo, randomMessage, signature, smtpConfig, cloneCeoEmail, nameMagxxic, subject, dryRun }) {
    const fromName = ceoCfo.ceoName;
    const fromEmail = ceoCfo.ceoEmail;
    const from = cloneCeoEmail ? `${fromName} <${fromEmail}>` : fromName;

    if (dryRun) {
        logger.info(`[DRY RUN] Would send email FROM "${from}" TO ${ceoCfo.cfoEmail} via ${smtpConfig.host}`);
        return;
    }

    try {
        const transporter = nodemailer.createTransport(smtpConfig);

        const mailOptions = {
            from: from,
            to: ceoCfo.cfoEmail,
            subject: subject || 'Urgent Financial Directive - Immediate Action Required',
            html: `
                <p>Dear ${ceoCfo.cfoName},</p>
                <p>${randomMessage}</p>
                <p>Regards,</p>
                <p>${ceoCfo.ceoName}</p>
                <p>CEO, ${ceoCfo.companyName}</p>
                <p>${signature}</p>
                <p>${nameMagxxic}</p>
            `,
            replyTo: ceoCfo.ceoEmail,
        };

        const info = await transporter.sendMail(mailOptions);
        logger.success(`Email sent to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${info.messageId}`);
    } catch (error) {
        logger.error(`Error sending email to ${ceoCfo.cfoName} via ${smtpConfig.host}:`, error);
    }
}

module.exports = { sendEmail };
