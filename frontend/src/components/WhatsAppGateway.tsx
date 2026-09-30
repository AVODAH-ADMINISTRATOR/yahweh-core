import { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';

export default function WhatsAppGateway() {
  const [qrLink, setQrLink] = useState('');
  const [command, setCommand] = useState('STATUS');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQR(command);
  }, [command]);

  const fetchQR = async (cmd: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/whatsapp-qr?command=${cmd}`);
      const data = await res.json();
      setQrLink(data.whatsapp_link);
    } catch (err) {
      console.error("Failed to fetch QR link", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="h-full flex flex-col">
      <h2 className="text-xl font-medium mb-6">WhatsApp Gateway</h2>
      <div className="flex-1 border p-8 bg-slate-50 flex flex-col items-center text-center justify-center">
        
        <div className="mb-8 w-full max-w-xs">
          <label className="block text-xs text-slate-500 uppercase tracking-widest mb-2 text-left">
            Select Command
          </label>
          <select 
            value={command} 
            onChange={(e) => setCommand(e.target.value)}
            className="w-full border p-3 focus:outline-none focus:border-corporate-blue text-sm bg-white"
          >
            <option value="STATUS">Check System Status (STATUS)</option>
            <option value="LOCK">Rotate Infrastructure Lock (LOCK)</option>
          </select>
        </div>

        <div className="bg-white p-4 border shadow-sm mb-8 min-h-[200px] flex items-center justify-center w-[200px]">
          {loading ? (
             <div className="animate-pulse h-32 w-32 bg-slate-200 rounded"></div>
          ) : (
            qrLink && <QRCodeSVG value={qrLink} size={168} level={"H"} />
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-slate-dark mb-2">Scan to Authenticate</p>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Scan this secure QR code with your mobile device to open a direct, encrypted WhatsApp tunnel to the compliance mainframe.
          </p>
        </div>

      </div>
    </section>
  );
}
