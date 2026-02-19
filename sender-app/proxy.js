const axios = require('axios');
const { SocksProxyAgent } = require('socks-proxy-agent');
const logger = require('./logger');

async function validateProxy(proxyUrl) {
    try {
        const agent = new SocksProxyAgent(proxyUrl);
        const response = await axios.get('https://api.ipify.org?format=json', {
            httpsAgent: agent,
            httpAgent: agent,
            timeout: 5000
        });
        if (response.data && response.data.ip) {
            return { valid: true, ip: response.data.ip };
        }
    } catch (err) {
        // Silent failure for validation
    }
    return { valid: false };
}

class ProxyRotator {
    constructor(proxies) {
        this.proxies = proxies || [];
        this.validProxies = [];
        this.index = 0;
    }

    async validateAll() {
        logger.info(`Validating ${this.proxies.length} proxies...`);
        const results = await Promise.all(this.proxies.map(p => validateProxy(p)));
        this.validProxies = this.proxies.filter((p, i) => results[i].valid);
        logger.info(`Found ${this.validProxies.length} valid proxies.`);
        return this.validProxies;
    }

    getNext() {
        if (this.validProxies.length === 0) return null;
        const proxy = this.validProxies[this.index];
        this.index = (this.index + 1) % this.validProxies.length;
        return proxy;
    }
}

module.exports = { ProxyRotator, validateProxy };
