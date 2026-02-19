const figlet = require('figlet');
const chalk = require('chalk');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const fs = require('fs');
const path = require('path');
const Table = require('cli-table3');
const logger = require('./logger');
const { readMailingList, sleep } = require('./utils');
const { sendEmail } = require('./email');
const { ProxyRotator } = require('./proxy');

function printBanner() {
    console.clear();
    const bannerText = figlet.textSync('MagxxicVox', { font: 'Standard' });
    console.log(chalk.blue(bannerText));
    console.log(chalk.yellow('    >>> ADVANCED SMTP UTILITY - STATUS: READY <<<'));
    console.log(chalk.green('    MODULAR MULTI-RELAY MAILER | v3.0.1\n'));
}

async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('dry-run', { type: 'boolean', description: 'Dry run mode', default: false })
        .help()
        .argv;

    printBanner();

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

    const { smtpConfigurations, proxies, mailingListPath, message, trackingUrl, customHeaders } = config;

    const absMailingListPath = path.isAbsolute(mailingListPath) ? mailingListPath : path.join(process.cwd(), mailingListPath);
    const mailingList = await readMailingList(absMailingListPath);

    if (mailingList.length === 0) {
        logger.warn('Mailing list is empty. Exiting.');
        return;
    }

    const rotator = new ProxyRotator(proxies);
    await rotator.validateAll();

    let stats = { success: 0, failed: 0, total: 0 };
    let smtpIndex = 0;

    const renderDashboard = () => {
        printBanner();
        const table = new Table({
            head: [chalk.cyan('Total'), chalk.green('Success'), chalk.red('Failed'), chalk.yellow('Remaining')],
            colWidths: [15, 15, 15, 15]
        });
        const remaining = mailingList.length - (stats.success + stats.failed);
        table.push([mailingList.length, stats.success, stats.failed, remaining >= 0 ? remaining : 0]);
        console.log(table.toString());
        console.log('\nLast status log:');
    };

    for (const recipient of mailingList) {
        const smtpConfig = smtpConfigurations[smtpIndex % smtpConfigurations.length];
        const proxy = rotator.getNext();

        const from = recipient.from || message.from;
        const subject = recipient.subject || message.subject;

        logger.info(`Sending to ${recipient.to} from ${from}...`);

        const result = await sendEmail({
            to: recipient.to,
            from: from,
            subject: subject,
            body: message.body,
            smtpConfig,
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

    logger.info('Task completed.');
}

main().catch(err => logger.error('Main error:', err));
