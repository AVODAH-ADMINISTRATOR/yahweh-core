const CDP = require('chrome-remote-interface');

async function linkInterface() {
    let client;
    try {
        client = await CDP({ port: 9222 });
        const { Page, Runtime } = client;

        await Page.enable();
        await Page.navigate({ url: 'https://example.com' });
        await Page.loadEventFired();
        
        console.log("Chrome instance successfully linked across console interface.");
    } catch (err) {
        console.error("Failed to establish cross-interface link:", err);
    } finally {
        if (client) await client.close();
    }
}

linkInterface();
