const fs = require('fs');
const readline = require('readline');

// Helper to parse CSV line correctly handling quotes and commas
function parseCSVLine(line) {
    const result = [];
    let cur = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuote = !inQuote;
        } else if (char === ',' && !inQuote) {
            result.push(cur.trim());
            cur = '';
        } else {
            cur += char;
        }
    }
    result.push(cur.trim());
    return result;
}

async function readMailingList(filePath) {
    const list = [];
    if (!fs.existsSync(filePath)) return list;
    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });
    for await (const line of rl) {
        if (!line.trim()) continue;
        const [to, from, subject, ...extra] = parseCSVLine(line);
        list.push({
            to: to?.replace(/^"|"$/g, ''),
            from: from?.replace(/^"|"$/g, ''),
            subject: subject?.replace(/^"|"$/g, ''),
            extra: extra.map(e => e.replace(/^"|"$/g, ''))
        });
    }
    return list;
}

async function readMessageDrafts(filePath) {
    const messageDrafts = [];
    if (!fs.existsSync(filePath)) return messageDrafts;
    const content = fs.readFileSync(filePath, 'utf-8');
    return content.split('---').map(d => d.trim()).filter(d => d);
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

module.exports = { readMailingList, readMessageDrafts, sleep };
