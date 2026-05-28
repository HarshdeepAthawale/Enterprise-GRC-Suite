import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardSummary, getDashboardHeatmap, triggerCheck } from '../lib/api';

interface Summary {
  total_controls: number;
  passing: number;
  failing: number;
  pass_rate: number;
  last_updated: string | null;
  by_function: { ref: string; title: string; total: number; passing: number; pass_rate: number }[];
  failing_controls: { control_ref: string; name: string; evidence_id: string; collected_at: string }[];
}

interface HeatmapEntry {
  function_ref: string;
  function_title: string;
  controls: { control_ref: string; name: string; passing: boolean }[];
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [rechecking, setRechecking] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [s, h] = await Promise.all([getDashboardSummary(), getDashboardHeatmap()]);
      setSummary(s);
      setHeatmap(h);
    } catch {
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleRecheck = async (controlRef: string) => {
    setRechecking(controlRef);
    try {
      // Find the control in heatmap to get its ID — but we need the DB ID.
      // For now, pass controlRef and let the backend resolve it.
      await triggerCheck(controlRef);
      await loadData();
    } finally {
      setRechecking(null);
    }
  };

  if (loading) return <div className="text-center py-12">Loading dashboard...</div>;

  const fnColors: Record<string, string> = {
    GV: 'bg-blue-500', ID: 'bg-cyan-500', PR: 'bg-green-500',
    DE: 'bg-yellow-500', RS: 'bg-orange-500', RC: 'bg-red-500',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Compliance Score" value={`${summary?.pass_rate ?? 0}%`} color="text-green-600" />
        <StatCard title="Controls Checked" value={summary?.total_controls ?? 0} color="text-blue-600" />
        <StatCard title="Passing" value={summary?.passing ?? 0} color="text-green-600" />
        <StatCard title="Failing" value={summary?.failing ?? 0} color="text-red-600" />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">NIST CSF 2.0 — Control Heat Map</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {heatmap.map((fn) => (
            <div key={fn.function_ref} className="border rounded-lg p-4">
              <div className="text-sm font-mono text-gray-500">{fn.function_ref}</div>
              <div className="text-sm font-medium truncate">{fn.function_title}</div>
              <div className={`text-2xl font-bold mt-2 ${fnColors[fn.function_ref] || 'bg-gray-500'} text-white px-2 py-1 rounded inline-block`}>
                {fn.controls.length > 0
                  ? Math.round((fn.controls.filter((c) => c.passing).length / fn.controls.length) * 100)
                  : 0}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {fn.controls.filter((c) => c.passing).length}/{fn.controls.length} passing
              </div>
            </div>
          ))}
        </div>
      </div>

      {summary && summary.failing_controls.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Failed Controls</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-mono">Control</th>
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Last Checked</th>
                  <th className="pb-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {summary.failing_controls.map((fc) => (
                  <tr key={fc.control_ref} className="border-b hover:bg-gray-50">
                    <td className="py-2 font-mono text-red-600">{fc.control_ref}</td>
                    <td className="py-2">
                      <button
                        onClick={() => navigate(`/controls/${fc.evidence_id}`)}
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        {fc.name}
                      </button>
                    </td>
                    <td className="py-2 text-gray-500">
                      {fc.collected_at ? new Date(fc.collected_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="py-2">
                      <button
                        onClick={() => handleRecheck(fc.control_ref)}
                        disabled={rechecking === fc.control_ref}
                        className="text-sm text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
                      >
                        {rechecking === fc.control_ref ? 'Running...' : 'Re-check'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="text-sm text-gray-500">{title}</div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
