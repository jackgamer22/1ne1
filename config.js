const fs = require('fs');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const logger = require('./logger');

function loadConfig() {
    const argv = yargs(hideBin(process.argv))
        .option('config', {
            alias: 'c',
            description: 'Path to the configuration file',
            type: 'string',
            default: 'config.json',
        })
        .argv;

    try {
        return JSON.parse(fs.readFileSync(argv.config, 'utf8'));
    } catch (error) {
        logger.error(`Error loading configuration from ${argv.config}: ${error.message}`);
        process.exit(1);
    }
}

module.exports = loadConfig();
