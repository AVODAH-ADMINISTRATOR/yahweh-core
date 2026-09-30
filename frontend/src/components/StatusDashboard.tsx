

export default function StatusDashboard({ status }: { status: any }) {
  if (!status) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-slate-200 rounded w-1/4"></div>
        <div className="h-24 bg-slate-100 rounded"></div>
      </div>
    );
  }

  return (
    <section>
      <h2 className="text-xl font-medium mb-6">System Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Core metrics */}
        <div className="p-6 border rounded-sm bg-slate-50 flex flex-col justify-between">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Deployment</p>
            <p className="text-2xl font-light text-corporate-blue">{status['System Deployment']}</p>
          </div>
          <div className="mt-8">
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Defense System</p>
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 bg-green-500 rounded-full"></span>
              <p className="font-medium text-slate-dark">{status['Defense Status']}</p>
            </div>
          </div>
        </div>

        {/* Threat profile */}
        <div className="p-6 border rounded-sm flex flex-col justify-between">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Threat Database</p>
            <p className="text-lg font-mono text-slate-700">{status['AI Threat Database']}</p>
          </div>
          <div className="mt-8 flex justify-between items-end">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Violations Logged</p>
              <p className="text-3xl font-light text-red-600">{status['Tamper Violations Logged']}</p>
            </div>
            <p className="text-xs text-slate-400">Since boot</p>
          </div>
        </div>

      </div>
    </section>
  );
}
