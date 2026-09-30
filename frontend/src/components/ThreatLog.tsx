import React, { useState } from 'react';

export default function ThreatLog() {
  const [payload, setPayload] = useState('');
  const [log, setLog] = useState<{timestamp: number, payload: string}[]>([]);
  const [responseMsg, setResponseMsg] = useState('');

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!payload.trim()) return;

    try {
      const res = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload }),
      });
      const data = await res.json();
      
      setResponseMsg(`[${data.status}] ${data.action}`);
      if (data.status === 'Violator Neutralized') {
        setLog([{ timestamp: Date.now(), payload }, ...log]);
        // Also refresh status page via window reload or passing up state (for demo we just log it)
      }
    } catch (err) {
      console.error(err);
      setResponseMsg("Failed to connect to AI Antivirus engine.");
    }
    setPayload('');
  };

  return (
    <section>
      <h2 className="text-xl font-medium mb-6">AI Antivirus Engine</h2>
      <div className="border p-6 bg-slate-50">
        
        <form onSubmit={handleScan} className="flex gap-4 mb-6">
          <input 
            type="text" 
            value={payload}
            onChange={e => setPayload(e.target.value)}
            placeholder="Simulate incoming payload (e.g., exec(bypass))"
            className="flex-1 border p-3 focus:outline-none focus:border-corporate-blue text-sm"
          />
          <button 
            type="submit"
            className="bg-corporate-blue text-white px-6 py-3 text-sm font-medium tracking-wide uppercase hover:bg-corporate-light-blue transition-colors"
          >
            Scan Payload
          </button>
        </form>

        {responseMsg && (
          <div className="mb-6 p-4 border-l-4 border-slate-400 bg-white text-sm font-mono text-slate-700">
            {responseMsg}
          </div>
        )}

        <div>
          <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Quarantine Log</p>
          <div className="bg-slate-dark text-green-400 font-mono text-xs p-4 h-48 overflow-y-auto">
            {log.length === 0 ? (
              <p className="text-slate-500">No threats detected. Integrity maintained.</p>
            ) : (
              log.map((item, idx) => (
                <div key={idx} className="mb-2">
                  <span className="text-slate-400">[{new Date(item.timestamp).toISOString()}]</span> 
                  <span className="text-red-400 ml-2">VIOLATOR PAYLOAD:</span> {item.payload}
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </section>
  );
}
