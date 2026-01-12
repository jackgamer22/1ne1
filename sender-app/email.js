const nodemailer = require('nodemailer');
const log = require('./logger');

async function sendEmail(ceoCfo, messageDrafts, signature, smtpConfig, cloneCeoEmail, nameMagxxic) {
    try {
        const transporter = nodemailer.createTransport(smtpConfig);
        const randomDelay = Math.floor(Math.random() * (15000 - 7000 + 1)) + 7000;
        await new Promise(resolve => setTimeout(resolve, randomDelay));

        const randomMessage = messageDrafts[Math.floor(Math.random() * messageDrafts.length)];

        let fromName = ceoCfo.ceoName;
        let fromEmail = ceoCfo.ceoEmail;

        const from = cloneCeoEmail ? `${fromName} <${fromEmail}>` : fromName;

        const mailOptions = {
            from: from,
            to: ceoCfo.cfoEmail,
            subject: 'Urgent Financial Directive - Immediate Action Required',
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
        log(`Email sent to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${info.messageId}`, 'success');
    } catch (error) {
        log(`Error sending email to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${error}`, 'error');
    }
}

module.exports = {
    sendEmail,
};
