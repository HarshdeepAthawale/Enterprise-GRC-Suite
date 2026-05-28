import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getControl, triggerCheck } from '../lib/api';

interface Evidence {
  id: string;
  collector_type: string;
  is_passing: boolean;
  pass_fail_reason: string;
  collected_at: string;
}

interface Control {
  id: string;
  control_ref: string;
  name: string;
  description: string;
  implementation_examples: string[];
  collectors: string[];
  evidence: Evidence[];
}

export default function ControlDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [control, setControl] = useState<Control | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = async () => {
    if (!id) return;
    const c = await getControl(id);
    setControl(c);
    setLoading(false);
  };

  useEffect(() => { load(); }, [id]);

  const handleCheck = async () => {
    if (!id) return;
    setRunning(true);
    try {
      await triggerCheck(id);
      await load();
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;
  if (!control) return <div className="text-center py-12">Control not found</div>;

  const latestEvidence = control.evidence[0];
  const chartData = computeTrend(control.evidence);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-gray-500 font-mono">{control.control_ref}</div>
          <h1 className="text-2xl font-bold text-gray-900">{control.name}</h1>
        </div>
        <button
          onClick={handleCheck}
          disabled={running}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {running ? 'Running...' : 'Run Check'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-2">Description</h2>
            <p className="text-gray-700">{control.description || 'No description available.'}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Evidence History</h2>
            {chartData.length > 0 && (
              <div className="flex items-end space-x-1 h-24 mb-4">
                {chartData.map((d, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-t ${d.passing ? 'bg-green-400' : 'bg-red-400'} hover:opacity-80 cursor-pointer`}
                    style={{ height: `${Math.max(d.count * 20, 8)}px` }}
                    title={`${d.label}: ${d.count} ${d.passing ? 'PASS' : 'FAIL'}`}
                  />
                ))}
              </div>
            )}
            {control.evidence.length === 0 && (
              <p className="text-gray-500">No evidence collected yet. Run a check to begin.</p>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Evidence Log</h2>
            <div className="space-y-2">
              {control.evidence.map((ev) => (
                <div
                  key={ev.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                  onClick={() => navigate(`/evidence/${ev.id}`)}
                >
                  <div>
                    <div className="text-sm font-mono text-gray-500">{ev.collector_type}</div>
                    <div className="text-sm">{ev.pass_fail_reason}</div>
                  </div>
                  <div className="text-right">
                    <div className={ev.is_passing ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                      {ev.is_passing ? 'PASS' : 'FAIL'}
                    </div>
                    <div className="text-xs text-gray-400">
                      {ev.collected_at ? new Date(ev.collected_at).toLocaleString() : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-2">Latest Status</h2>
            {latestEvidence ? (
              <>
                <div className={`text-2xl font-bold ${latestEvidence.is_passing ? 'text-green-600' : 'text-red-600'}`}>
                  {latestEvidence.is_passing ? 'PASSING' : 'FAILING'}
                </div>
                <div className="text-sm text-gray-500 mt-1">{latestEvidence.pass_fail_reason}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {latestEvidence.collected_at ? new Date(latestEvidence.collected_at).toLocaleString() : ''}
                </div>
              </>
            ) : (
              <div className="text-gray-500">No checks run yet</div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-2">Configuration</h2>
            {control.implementation_examples && control.implementation_examples.length > 0 && (
              <div className="mt-2">
                <div className="text-sm font-medium text-gray-700">Implementation Examples:</div>
                <ul className="list-disc pl-4 text-sm text-gray-600 space-y-1 mt-1">
                  {control.implementation_examples.slice(0, 5).map((ex: any, i: number) => (
                    <li key={i}>{typeof ex === 'string' ? ex : JSON.stringify(ex)}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function computeTrend(evidence: Evidence[]) {
  const buckets: Record<string, { label: string; passing: number; failing: number }> = {};
  for (const ev of evidence) {
    if (!ev.collected_at) continue;
    const day = ev.collected_at.split('T')[0];
    if (!buckets[day]) buckets[day] = { label: day, passing: 0, failing: 0 };
    if (ev.is_passing) buckets[day].passing++;
    else buckets[day].failing++;
  }
  return Object.values(buckets).reverse().slice(0, 14).map((b) => ({
    label: b.label.slice(5),
    count: b.passing + b.failing,
    passing: b.passing > b.failing,
  }));
}
