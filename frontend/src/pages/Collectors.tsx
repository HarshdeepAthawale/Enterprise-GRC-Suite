import { useEffect, useState } from 'react';
import { getCollectors, saveCollectorConfig } from '../lib/api';

interface Collector {
  type: string;
  description: string;
  version: string;
  controls: string[];
}

export default function Collectors() {
  const [collectors, setCollectors] = useState<Collector[]>([]);
  const [loading, setLoading] = useState(true);
  const [configs, setConfigs] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    getCollectors()
      .then(setCollectors)
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (type: string) => {
    setSaving(type);
    try {
      const raw = configs[type] || '{}';
      const config = JSON.parse(raw);
      await saveCollectorConfig(type, config);
    } catch {
      alert('Invalid JSON config');
    } finally {
      setSaving(null);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Collectors</h1>

      <div className="grid gap-4 md:grid-cols-2">
        {collectors.map((c) => (
          <div key={c.type} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="font-mono text-sm text-indigo-600">{c.type}</div>
                <div className="text-sm text-gray-500">v{c.version}</div>
              </div>
              <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                {c.controls.length} control{c.controls.length !== 1 ? 's' : ''}
              </span>
            </div>

            <p className="text-sm text-gray-700 mb-3">{c.description}</p>

            <div className="text-xs text-gray-500 mb-3">
              Mapped controls:{' '}
              {c.controls.map((ref) => (
                <span key={ref} className="font-mono bg-gray-100 px-1 py-0.5 rounded mr-1">
                  {ref}
                </span>
              ))}
            </div>

            <div className="space-y-2">
              <label className="text-xs text-gray-500">Configuration (JSON)</label>
              <textarea
                rows={3}
                value={configs[c.type] || ''}
                onChange={(e) => setConfigs({ ...configs, [c.type]: e.target.value })}
                placeholder='{"access_key_id": "...", "secret_access_key": "..."}'
                className="w-full text-xs font-mono p-2 border rounded"
              />
              <button
                onClick={() => handleSave(c.type)}
                disabled={saving === c.type}
                className="text-sm text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
              >
                {saving === c.type ? 'Saving...' : 'Save Config'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
