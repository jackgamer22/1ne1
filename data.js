const fs = require('fs');
const readline = require('readline');
const { parse } = require('csv-parse');
const logger = require('./logger');

async function readCeoCfoPairs(filePath) {
    if (!fs.existsSync(filePath)) {
        logger.error(`CEO/CFO data file not found at: ${filePath}`);
        process.exit(1);
    }

    const records = [];
    const parser = fs.createReadStream(filePath).pipe(parse({
        columns: true,
        skip_empty_lines: true,
    }));

    for await (const record of parser) {
        if (record.ceoName && record.ceoEmail && record.companyName && record.cfoName && record.cfoEmail) {
            records.push(record);
        } else {
            logger.warn('Skipping invalid CSV record:', { record });
        }
    }
    return records;
}

async function readMessageDrafts(filePath) {
    if (!fs.existsSync(filePath)) {
        logger.error(`Message drafts file not found at: ${filePath}`);
        process.exit(1);
    }

    const messageDrafts = [];
    const fileStream = fs.createReadStream(filePath);

    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity,
    });

    let currentDraft = '';
    for await (const line of rl) {
        if (line.trim() === '---') {
            if (currentDraft) {
                messageDrafts.push(currentDraft.trim());
                currentDraft = '';
            }
        } else {
            currentDraft += line + '\n';
        }
    }
    if (currentDraft) {
        messageDrafts.push(currentDraft.trim());
    }

    return messageDrafts;
}

module.exports = { readCeoCfoPairs, readMessageDrafts };
