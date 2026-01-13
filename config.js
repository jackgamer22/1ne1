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
        const config = JSON.parse(fs.readFileSync(argv.config, 'utf8'));

        // Validate config
        const requiredKeys = [
            'smtpConfigurations', 'ceoCfoFilePath', 'messageDraftsPath',
            'signature', 'cloneCeoEmail', 'nameMagxxic', 'minDelay', 'maxDelay', 'emailPause'
        ];

        for (const key of requiredKeys) {
            if (!(key in config)) {
                throw new Error(`Missing required configuration key: ${key}`);
            }
        }

        return config;
    } catch (error) {
        logger.error(`Error loading or validating configuration from ${argv.config}: ${error.message}`);
        process.exit(1);
    }
}

module.exports = loadConfig();
