import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFrameworks, getControls } from '../lib/api';

interface Framework {
  id: string;
  name: string;
  version: string;
  control_count: number;
  imported_at: string;
}

export default function Frameworks() {
  const navigate = useNavigate();
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [controls, setControls] = useState<any[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFrameworks()
      .then(setFrameworks)
      .catch(() => navigate('/login'))
      .finally(() => setLoading(false));
  }, []);

  const selectFramework = async (id: string) => {
    setSelectedFramework(id);
    const c = await getControls(id);
    setControls(c);
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Frameworks</h1>

      <div className="grid gap-4 md:grid-cols-2">
        {frameworks.map((fw) => (
          <div
            key={fw.id}
            className={`bg-white rounded-lg shadow p-6 cursor-pointer border-2 ${
              selectedFramework === fw.id ? 'border-indigo-500' : 'border-transparent'
            }`}
            onClick={() => selectFramework(fw.id)}
          >
            <div className="text-lg font-semibold">{fw.name}</div>
            <div className="text-sm text-gray-500">v{fw.version}</div>
            <div className="text-sm text-gray-500">{fw.control_count} controls</div>
            <div className="text-xs text-gray-400 mt-1">
              Imported: {fw.imported_at ? new Date(fw.imported_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
        ))}
      </div>

      {controls.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            Controls ({controls.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-mono">ID</th>
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Function</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Last Checked</th>
                </tr>
              </thead>
              <tbody>
                {controls.map((c: any) => (
                  <tr
                    key={c.id}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/controls/${c.id}`)}
                  >
                    <td className="py-2 font-mono text-xs">{c.control_ref}</td>
                    <td className="py-2">{c.name}</td>
                    <td className="py-2 text-xs text-gray-500">{c.function_ref}</td>
                    <td className="py-2">
                      {c.latest_status === null && <span className="text-gray-400">——</span>}
                      {c.latest_status === true && <span className="text-green-600 font-medium">PASS</span>}
                      {c.latest_status === false && <span className="text-red-600 font-medium">FAIL</span>}
                    </td>
                    <td className="py-2 text-xs text-gray-500">
                      {c.last_checked ? new Date(c.last_checked).toLocaleString() : 'Never'}
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
