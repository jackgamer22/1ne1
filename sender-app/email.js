const nodemailer = require('nodemailer');
const { SocksProxyAgent } = require('socks-proxy-agent');
const logger = require('./logger');
const crypto = require('crypto');

async function sendEmail({
    ceoCfo,
    randomMessage,
    signature,
    smtpConfig,
    cloneCeoEmail,
    nameMagxxic,
    subject,
    proxy,
    trackingUrl,
    customHeaders,
    dryRun
}) {
    const fromName = ceoCfo.ceoName;
    const fromEmail = ceoCfo.ceoEmail;
    const from = cloneCeoEmail ? `${fromName} <${fromEmail}>` : fromName;

    if (dryRun) {
        logger.info(`[DRY RUN] From: "${from}" | To: ${ceoCfo.cfoEmail} | Proxy: ${proxy || 'None'}`);
        return true;
    }

    try {
        const transportOptions = { ...smtpConfig };
        if (proxy) {
            transportOptions.agent = new SocksProxyAgent(proxy);
        }

        const transporter = nodemailer.createTransport(transportOptions);

        // Tracking pixel
        const trackingPixel = trackingUrl ? `<img src="${trackingUrl}?id=${ceoCfo.cfoEmail}&t=${Date.now()}" width="1" height="1" style="display:none" />` : '';

        // Randomize Message-ID for spam evasion
        const messageId = `<${crypto.randomBytes(16).toString('hex')}@${smtpConfig.host}>`;

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
                ${trackingPixel}
            `,
            replyTo: ceoCfo.ceoEmail,
            messageId: messageId,
            headers: {
                'X-Mailer': `MagxxicVox v2.0-${crypto.randomBytes(4).toString('hex')}`,
                'List-Unsubscribe': `<mailto:unsubscribe@${ceoCfo.companyName.toLowerCase().replace(/\s+/g, '')}.com>`,
                ...customHeaders
            }
        };

        const info = await transporter.sendMail(mailOptions);
        logger.success(`Email sent to ${ceoCfo.cfoName} via ${smtpConfig.host}: ${info.messageId}`);
        return true;
    } catch (error) {
        logger.error(`Error sending email to ${ceoCfo.cfoName} via ${smtpConfig.host}:`, error);
        return false;
    }
}

module.exports = { sendEmail };
