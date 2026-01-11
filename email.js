const nodemailer = require('nodemailer');
const logger = require('./logger');

const smtpStatus = new Map();

function getNextSmtpConfig(configs) {
    const now = Date.now();
    const healthyConfigs = configs.filter(config => {
        if (!smtpStatus.has(config.host)) {
            return true;
        }
        const status = smtpStatus.get(config.host);
        return status.healthy || now > status.retryAfter;
    });

    if (healthyConfigs.length === 0) {
        logger.warn('No healthy SMTP servers available. Waiting for servers to recover.');
        return null;
    }

    // Simple rotation among healthy servers
    return healthyConfigs[Math.floor(Math.random() * healthyConfigs.length)];
}

function markSmtpAsUnhealthy(config) {
    const retryAfter = Date.now() + 5 * 60 * 1000; // 5 minutes
    smtpStatus.set(config.host, { healthy: false, retryAfter });
    logger.warn(`SMTP server ${config.host} marked as unhealthy. Will retry after 5 minutes.`);
}

async function sendEmail(ceoCfo, messageDrafts, config, smtpConfig) {
    try {
        const { minDelay, maxDelay, signature, cloneCeoEmail, nameMagxxic } = config;
        const transporter = nodemailer.createTransport(smtpConfig);
        const randomDelay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
        await new Promise(resolve => setTimeout(resolve, randomDelay));

        const randomMessage = messageDrafts[Math.floor(Math.random() * messageDrafts.length)];
        const from = cloneCeoEmail ? `${ceoCfo.ceoName} <${ceoCfo.ceoEmail}>` : ceoCfo.ceoName;

        const mailOptions = {
            from,
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
        logger.info(`Email sent to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${info.messageId}`);
        smtpStatus.set(smtpConfig.host, { healthy: true });
        return true;
    } catch (error) {
        logger.error(`Error sending email to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${error.message}`);
        markSmtpAsUnhealthy(smtpConfig);
        return false;
    }
}

module.exports = { sendEmail, getNextSmtpConfig };
