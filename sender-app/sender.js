const figlet = require('figlet');
const chalk = require('chalk');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const fs = require('fs');
const path = require('path');
const logger = require('./logger');
const { readCeoCfoPairs, readMessageDrafts, sleep } = require('./utils');
const { sendEmail } = require('./email');

async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('clone', { type: 'boolean', description: 'Clone CEO Email', default: false })
        .option('dry-run', { type: 'boolean', description: 'Dry run mode', default: false })
        .help()
        .argv;

    const banner = figlet.textSync('Magxxic CEO - CFO SENDER', { font: 'ANSI Shadow' });
    console.log(chalk.red(banner));

    const configPath = path.join(__dirname, 'config.json');
    if (!fs.existsSync(configPath)) {
        logger.error('config.json not found! Please create it based on config.example.json');
        process.exit(1);
    }

    let config;
    try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    } catch (err) {
        logger.error('Failed to parse config.json', err);
        process.exit(1);
    }

    const { smtpConfigurations, ceoCfoFilePath, messageDraftsPath, signature, nameMagxxic } = config;

    // Resolve paths relative to the current working directory if they are not absolute
    const absCeoCfoFilePath = path.isAbsolute(ceoCfoFilePath) ? ceoCfoFilePath : path.join(process.cwd(), ceoCfoFilePath);
    const absMessageDraftsPath = path.isAbsolute(messageDraftsPath) ? messageDraftsPath : path.join(process.cwd(), messageDraftsPath);

    const ceoCfoPairs = await readCeoCfoPairs(absCeoCfoFilePath);
    const messageDrafts = await readMessageDrafts(absMessageDraftsPath);

    if (ceoCfoPairs.length === 0) {
        logger.warn('No CEO-CFO pairs found.');
        return;
    }

    if (messageDrafts.length === 0) {
        logger.warn('No message drafts found.');
        return;
    }

    const companyMap = new Map();
    ceoCfoPairs.forEach(pair => {
        if (!companyMap.has(pair.companyName)) {
            companyMap.set(pair.companyName, []);
        }
        companyMap.get(pair.companyName).push(pair);
    });

    let smtpIndex = 0;
    for (const [companyName, pairs] of companyMap) {
        // Find entries that have CEO and CFO information.
        // They could be on the same line or separate lines.
        const ceoEntry = pairs.find(p => p.ceoName && p.ceoEmail);
        const cfoEntry = pairs.find(p => p.cfoName && p.cfoEmail);

        if (ceoEntry && cfoEntry) {
            const combined = {
                ceoName: ceoEntry.ceoName,
                ceoEmail: ceoEntry.ceoEmail,
                companyName: companyName,
                cfoName: cfoEntry.cfoName,
                cfoEmail: cfoEntry.cfoEmail
            };

            const smtpConfig = smtpConfigurations[smtpIndex % smtpConfigurations.length];
            const randomMessage = messageDrafts[Math.floor(Math.random() * messageDrafts.length)];

            const delay = Math.floor(Math.random() * (15000 - 7000 + 1)) + 7000;
            logger.info(`Waiting ${delay}ms before sending to ${combined.cfoName} (${companyName})...`);
            if (!argv['dry-run']) {
                await sleep(delay);
            }

            await sendEmail({
                ceoCfo: combined,
                randomMessage,
                signature,
                smtpConfig,
                cloneCeoEmail: argv.clone,
                nameMagxxic,
                subject: config.subject,
                dryRun: argv['dry-run']
            });

            smtpIndex++;
            if (!argv['dry-run']) {
                await sleep(2000);
            }
        } else {
            logger.warn(`Skipping ${companyName} due to missing CEO or CFO information.`);
        }
    }
}

main().catch(err => logger.error('Main loop error:', err));
