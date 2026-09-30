// A proxy object that safely absorbs all property accesses, method calls, and constructor invocations
// This allows the Vibe Code to use missing modules without crashing.
const dummyProxy = new Proxy(function() {}, {
    get: (target, prop) => {
        if (prop === 'then') return undefined; // Prevent infinite promise chains
        if (prop === '__esModule') return true;
        return dummyProxy;
    },
    apply: () => dummyProxy,
    construct: () => dummyProxy
});

module.exports = dummyProxy;
