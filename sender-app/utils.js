const fs = require('fs');
const readline = require('readline');

async function readCeoCfoPairs(filePath) {
    const ceoCfoPairs = [];
    if (!fs.existsSync(filePath)) return ceoCfoPairs;
    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });
    for await (const line of rl) {
        if (!line.trim()) continue;
        const [ceoName, ceoEmail, companyName, cfoName, cfoEmail] = line.split(',');
        ceoCfoPairs.push({
            ceoName: ceoName?.trim(),
            ceoEmail: ceoEmail?.trim(),
            companyName: companyName?.trim(),
            cfoName: cfoName?.trim(),
            cfoEmail: cfoEmail?.trim(),
        });
    }
    return ceoCfoPairs;
}

async function readMessageDrafts(filePath) {
    const messageDrafts = [];
    if (!fs.existsSync(filePath)) return messageDrafts;
    const content = fs.readFileSync(filePath, 'utf-8');
    return content.split('---').map(d => d.trim()).filter(d => d);
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

module.exports = { readCeoCfoPairs, readMessageDrafts, sleep };
