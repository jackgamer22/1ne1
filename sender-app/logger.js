const chalk = require('chalk');
const fs = require('fs');
const path = require('path');

const logFile = path.join(process.cwd(), 'sender.log');

const logger = {
    info: (msg) => {
        console.log(chalk.blue(msg));
        fs.appendFileSync(logFile, `[INFO] ${new Date().toISOString()} - ${msg}\n`);
    },
    success: (msg) => {
        console.log(chalk.green(msg));
        fs.appendFileSync(logFile, `[SUCCESS] ${new Date().toISOString()} - ${msg}\n`);
    },
    warn: (msg) => {
        console.log(chalk.yellow(msg));
        fs.appendFileSync(logFile, `[WARN] ${new Date().toISOString()} - ${msg}\n`);
    },
    error: (msg, err) => {
        console.error(chalk.red(msg), err || '');
        fs.appendFileSync(logFile, `[ERROR] ${new Date().toISOString()} - ${msg} ${err ? (err.stack || err) : ''}\n`);
    }
};

module.exports = logger;
