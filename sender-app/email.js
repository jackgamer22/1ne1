const nodemailer = require('nodemailer');
const { SocksProxyAgent } = require('socks-proxy-agent');
const logger = require('./logger');
const crypto = require('crypto');

async function sendEmail({
    to,
    from,
    subject,
    body,
    smtpConfig,
    proxy,
    trackingUrl,
    customHeaders,
    dryRun
}) {
    if (dryRun) {
        logger.info(`[DRY RUN] From: "${from}" | To: ${to} | Proxy: ${proxy || 'None'}`);
        return true;
    }

    try {
        const transportOptions = { ...smtpConfig };
        if (proxy) {
            transportOptions.agent = new SocksProxyAgent(proxy);
        }

        const transporter = nodemailer.createTransport(transportOptions);

        // Tracking pixel
        const trackingPixel = trackingUrl ? `<img src="${trackingUrl}?id=${to}&t=${Date.now()}" width="1" height="1" style="display:none" />` : '';

        // Randomize Message-ID for deliverability
        const messageId = `<${crypto.randomBytes(16).toString('hex')}@${smtpConfig.host}>`;

        const mailOptions = {
            from: from,
            to: to,
            subject: subject,
            html: `${body}${trackingPixel}`,
            messageId: messageId,
            headers: {
                'X-Mailer': `Generic-Mailer-v2.0-${crypto.randomBytes(4).toString('hex')}`,
                ...customHeaders
            }
        };

        const info = await transporter.sendMail(mailOptions);
        logger.success(`Email sent to ${to} via ${smtpConfig.host}: ${info.messageId}`);
        return true;
    } catch (error) {
        logger.error(`Error sending email to ${to} via ${smtpConfig.host}:`, error);
        return false;
    }
}

module.exports = { sendEmail };
