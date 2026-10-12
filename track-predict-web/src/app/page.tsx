'use client';

import { useEffect, useState } from 'react';

interface ForecastItem {
  event_title: string;
  venue: string;
  start_time: string;
  predicted_customers: number;
  peak_rush_time: string;
}

export default function Dashboard() {
  const [forecast, setForecast] = useState<ForecastItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/forecast')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          setForecast(data.data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching forecast:', err);
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="border-b border-slate-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight text-white">Track-Predict</h1>
          <p className="text-slate-400 text-sm mt-1">24-Hour Local Traffic & Rush Inferences for York</p>
        </header>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading forecast metrics...</div>
        ) : (
          <div className="grid gap-4">
            {forecast.map((item, idx) => (
              <div key={idx} className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-5 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {item.start_time}
                  </span>
                  <h2 className="text-lg font-semibold text-white pt-1">{item.event_title}</h2>
                  <p className="text-sm text-slate-400">{item.venue}</p>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-400">~{item.predicted_customers}</div>
                  <div className="text-xs text-slate-400">Expected Rush @ {item.peak_rush_time}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
