const Module = require('module');
const path = require('path');

const originalResolve = Module._resolveFilename;

// Override require to intercept missing modules
Module._resolveFilename = function(request, parent, isMain, options) {
    if (request.startsWith('@antigravity/') || 
        request.startsWith('cloudflare/') || 
        request.startsWith('firebase/') ||
        request.startsWith('@google/') ||
        request.startsWith('@microsoft/')) {
        return path.resolve(__dirname, 'dummy_module.js');
    }
    return originalResolve.apply(this, arguments);
};
