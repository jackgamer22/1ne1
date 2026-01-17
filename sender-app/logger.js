const fs = require('fs');
const chalk = require('chalk');

const logFilePath = 'sender.log';

function log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const formattedMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

    // Log to console with colors
    switch (level) {
        case 'info':
            console.log(chalk.blue(formattedMessage));
            break;
        case 'success':
            console.log(chalk.green(formattedMessage));
            break;
        case 'warn':
            console.log(chalk.yellow(formattedMessage));
            break;
        case 'error':
            console.log(chalk.red(formattedMessage));
            break;
        default:
            console.log(formattedMessage);
    }

    // Append to log file
    fs.appendFileSync(logFilePath, formattedMessage + '\n');
}

module.exports = log;
