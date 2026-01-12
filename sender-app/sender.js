const figlet = require('figlet');
const chalk = require('chalk');
const { readCeoCfoPairs, readMessageDrafts } = require('./utils');
const yargs = require('yargs');
const { sendEmail } = require('./email');
const fs = require('fs');

// Generate the banner
if (!fs.existsSync('./config.json')) {
    console.error('Error: config.json not found. Please create it by copying config.example.json.');
    process.exit(1);
}
const config = require('./config.json');

const log = require('./logger');

const banner = figlet.textSync('Magxxic CEO - CFO SENDER', { font: 'ANSI Shadow' });
log(banner, 'info');

const argv = yargs
    .option('clone', {
        alias: 'c',
        description: 'Clone the CEO email',
        type: 'boolean',
        default: config.cloneCeoEmail,
    })
    .option('dry-run', {
        alias: 'd',
        description: 'Simulate sending emails without actually sending them',
        type: 'boolean',
        default: false,
    })
    .help()
    .alias('help', 'h')
    .argv;

// SMTP Configurations - The more, the merrier!
const { smtpConfigurations, ceoCfoFilePath, messageDraftsPath, signature, nameMagxxic } = config;

async function main() {
    const ceoCfoPairs = await readCeoCfoPairs(ceoCfoFilePath);

    // Group CEO-CFO pairs by company - Divide and conquer!
    const companyMap = new Map();
    ceoCfoPairs.forEach(pair => {
        if (!companyMap.has(pair.companyName)) {
            companyMap.set(pair.companyName, []);
        }
        companyMap.get(pair.companyName).push(pair);
    });

    const messageDrafts = await readMessageDrafts(messageDraftsPath);
    let smtpIndex = 0;
    let sentEmails = 0;

    // Iterate through each company - Spreading chaos far and wide!
    for (const [companyName, pairs] of companyMap) {
        // Ensure there's a CEO and CFO for this company - Can't leave anyone out!
        if (pairs.length >= 2) {
            const ceo = pairs[0]; // Assuming the first entry is the CEO
            const cfo = pairs.find(pair => pair.cfoEmail); // Find the CFO entry

            if (ceo && cfo) {
                const smtpConfig = smtpConfigurations[smtpIndex % smtpConfigurations.length];
                if (argv.dryRun) {
                    log(`--dry-run: Would send email to ${cfo.cfoName} via ${smtpConfig.host}`, 'warn');
                } else {
                    const success = await sendEmail(cfo, messageDrafts, signature, smtpConfig, argv.clone, nameMagxxic);
                    if (success) {
                        sentEmails++;
                    }
                }
                smtpIndex++;
                await new Promise(resolve => setTimeout(resolve, 2000)); // Pause for 2 seconds between emails - Gotta savor the moment!
            } else {
                log(`Skipping ${companyName} due to missing CEO or CFO.`, 'warn');
            }
        } else {
            log(`Skipping ${companyName} due to insufficient data.`, 'warn');
        }
    }

    log(`Finished sending emails. Total sent: ${sentEmails}`, 'info');
}

main().catch(err => log(err, 'error'));
