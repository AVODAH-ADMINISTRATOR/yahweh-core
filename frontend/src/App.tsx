import { useState, useEffect } from 'react'
import StatusDashboard from './components/StatusDashboard'
import ThreatLog from './components/ThreatLog'
import WhatsAppGateway from './components/WhatsAppGateway'

function App() {
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/status')
      .then(res => res.json())
      .then(data => setSystemStatus(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-white text-slate-dark font-sans p-8 md:p-16">
      {/* Header */}
      <header className="mb-16 border-b pb-8">
        <h1 className="text-4xl font-light tracking-tight text-corporate-blue">
          Integrated Avodah LLC
        </h1>
        <p className="text-sm text-slate-gray mt-2 uppercase tracking-widest">
          Corporate Compliance Portal
        </p>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-12">
          <StatusDashboard status={systemStatus} />
          <ThreatLog />
        </div>
        
        <div className="lg:col-span-1 border-l pl-0 lg:pl-12">
          <WhatsAppGateway />
        </div>
      </main>
    </div>
  )
}

export default App
