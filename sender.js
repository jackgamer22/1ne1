
const figlet = require('figlet');
const figlet = require('figlet');
const chalk = require('chalk');
const logger = require('./logger');
const config = require('./config');
const { readCeoCfoPairs, readMessageDrafts } = require('./data');
const { sendEmail, getNextSmtpConfig } = require('./email');

async function main() {
    // Generate the banner
    const banner = figlet.textSync('Magxxic CEO - CFO SENDER', { font: 'ANSI Shadow' });
    logger.info(chalk.red(banner));

    const { smtpConfigurations, emailPause } = config;

    const ceoCfoPairs = await readCeoCfoPairs(config.ceoCfoFilePath);
    const messageDrafts = await readMessageDrafts(config.messageDraftsPath);

    // Group CEO-CFO pairs by company
    const companyMap = new Map();
    ceoCfoPairs.forEach(pair => {
        if (!companyMap.has(pair.companyName)) {
            companyMap.set(pair.companyName, []);
        }
        companyMap.get(pair.companyName).push(pair);
    });

    // Iterate through each company
    for (const [companyName, pairs] of companyMap) {
        if (pairs.length >= 2) {
            const ceo = pairs[0];
            const cfo = pairs.find(pair => pair.cfoEmail);

            if (ceo && cfo) {
                const smtpConfig = getNextSmtpConfig(smtpConfigurations);
                if (smtpConfig) {
                    await sendEmail(cfo, messageDrafts, config, smtpConfig);
                    await new Promise(resolve => setTimeout(resolve, emailPause));
                } else {
                    logger.error('Halting execution: No healthy SMTP servers available.');
                    break;
                }
            } else {
                logger.warn(`Skipping ${companyName} due to missing CEO or CFO.`);
            }
        } else {
            logger.warn(`Skipping ${companyName} due to insufficient data.`);
        }
    }
}

main().catch(err => {
    logger.error(`Unhandled error in main function: ${err.message}`);
});
