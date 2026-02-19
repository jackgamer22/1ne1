const figlet = require('figlet');
const chalk = require('chalk');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const fs = require('fs');
const path = require('path');
const Table = require('cli-table3');
const logger = require('./logger');
const { readCeoCfoPairs, readMessageDrafts, sleep } = require('./utils');
const { sendEmail } = require('./email');
const { ProxyRotator } = require('./proxy');

async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('clone', { type: 'boolean', description: 'Clone CEO Email', default: false })
        .option('dry-run', { type: 'boolean', description: 'Dry run mode', default: false })
        .help()
        .argv;

    // Artistic Banner
    console.clear();
    const logo = `
          @@@@      @@@@@@@@@@@@@@@@      @@@@
          @@@@      @@@@@@@@@@@@@@@@      @@@@
                    @@@@@@@@@@@@@@@@
                        @@@@@@@@
                    @@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@
                @@@@@@@@@@@@@@@@@@@@@@@@
    `;
    console.log(chalk.red(logo));

    const bannerText = figlet.textSync('MagxxicVox', { font: 'ANSI Shadow' });
    console.log(chalk.blue(bannerText));

    console.log(chalk.yellow('    >>> PROXY-ONLY DIRECT-TO-MX DELIVERY SYSTEM - STATUS: ARMED <<<'));
    console.log(chalk.cyan('    [RFC-2822] [DKIM-SIGNED] [SOCKS5-CHAIN] [ZERO-SMTP-RELAY]'));
    console.log(chalk.green('    VERSION 2.0.0 | BUILD 2026-02-19 | CEO to CFO, HR Mass sender\n'));

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

    const { smtpConfigurations, proxies, ceoCfoFilePath, messageDraftsPath, signature, nameMagxxic, subject, trackingUrl, customHeaders } = config;

    const absCeoCfoFilePath = path.isAbsolute(ceoCfoFilePath) ? ceoCfoFilePath : path.join(process.cwd(), ceoCfoFilePath);
    const absMessageDraftsPath = path.isAbsolute(messageDraftsPath) ? messageDraftsPath : path.join(process.cwd(), messageDraftsPath);

    const ceoCfoPairs = await readCeoCfoPairs(absCeoCfoFilePath);
    const messageDrafts = await readMessageDrafts(absMessageDraftsPath);

    if (ceoCfoPairs.length === 0 || messageDrafts.length === 0) {
        logger.warn('Missing data (pairs or drafts). Exiting.');
        return;
    }

    // Proxy setup
    const rotator = new ProxyRotator(proxies);
    await rotator.validateAll();

    const companyMap = new Map();
    ceoCfoPairs.forEach(pair => {
        if (!companyMap.has(pair.companyName)) companyMap.set(pair.companyName, []);
        companyMap.get(pair.companyName).push(pair);
    });

    let stats = { success: 0, failed: 0, total: 0 };
    let smtpIndex = 0;

    const renderDashboard = () => {
        const table = new Table({
            head: [chalk.cyan('Total'), chalk.green('Success'), chalk.red('Failed'), chalk.yellow('Remaining')],
            colWidths: [15, 15, 15, 15]
        });
        const remaining = Array.from(companyMap.keys()).length - (stats.success + stats.failed);
        table.push([stats.total, stats.success, stats.failed, remaining >= 0 ? remaining : 0]);
        console.log('\n' + table.toString());
    };

    for (const [companyName, pairs] of companyMap) {
        const ceoEntry = pairs.find(p => p.ceoName && p.ceoEmail);
        const cfoEntry = pairs.find(p => p.cfoName && p.cfoEmail);

        if (ceoEntry && cfoEntry) {
            stats.total++;
            const combined = {
                ceoName: ceoEntry.ceoName,
                ceoEmail: ceoEntry.ceoEmail,
                companyName: companyName,
                cfoName: cfoEntry.cfoName,
                cfoEmail: cfoEntry.cfoEmail
            };

            const smtpConfig = smtpConfigurations[smtpIndex % smtpConfigurations.length];
            const randomMessage = messageDrafts[Math.floor(Math.random() * messageDrafts.length)];
            const proxy = rotator.getNext();

            const delay = Math.floor(Math.random() * (15000 - 7000 + 1)) + 7000;
            logger.info(`[${companyName}] Sending to ${combined.cfoName}...`);

            if (!argv['dry-run']) await sleep(delay);

            const result = await sendEmail({
                ceoCfo: combined,
                randomMessage,
                signature,
                smtpConfig,
                cloneCeoEmail: argv.clone,
                nameMagxxic,
                subject,
                proxy,
                trackingUrl,
                customHeaders,
                dryRun: argv['dry-run']
            });

            if (result) stats.success++; else stats.failed++;
            smtpIndex++;
            renderDashboard();

            if (!argv['dry-run']) await sleep(2000);
        }
    }

    logger.info('Task completed.');
}

main().catch(err => logger.error('Main loop error:', err));
