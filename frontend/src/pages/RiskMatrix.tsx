import { useEffect, useState } from 'react';
import { getRiskMatrix, updateRiskMatrix } from '../lib/api';

export default function RiskMatrixPage() {
  const [matrix, setMatrix] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getRiskMatrix()
      .then(setMatrix)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-12">Loading...</div>;

  const grid = matrix?.matrix || [];
  const likelihood = matrix?.likelihood_labels || [];
  const impact = matrix?.impact_labels || [];

  const getColor = (val: number) => {
    if (val <= 4) return 'bg-green-200 text-green-900';
    if (val <= 9) return 'bg-yellow-200 text-yellow-900';
    if (val <= 15) return 'bg-orange-200 text-orange-900';
    return 'bg-red-200 text-red-900';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Risk Matrix</h1>
        <button
          onClick={async () => {
            setSaving(true);
            await updateRiskMatrix(matrix);
            setSaving(false);
          }}
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">{matrix?.name || '5x5 Risk Matrix'}</h2>

        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 border bg-gray-50 text-gray-600 font-medium">Likelihood ↓ / Impact →</th>
                {impact.map((label: string, i: number) => (
                  <th key={i} className="p-2 border bg-gray-50 text-gray-600 font-medium text-center">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.map((row: number[], li: number) => (
                <tr key={li}>
                  <td className="p-2 border bg-gray-50 text-gray-600 font-medium">{likelihood[li]}</td>
                  {row.map((val, ii) => (
                    <td
                      key={ii}
                      className={`p-3 border text-center font-bold text-lg ${getColor(val)}`}
                      title={`${likelihood[li]} × ${impact[ii]} = ${val}`}
                    >
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center space-x-4 text-sm">
          <span className="flex items-center"><span className="w-3 h-3 bg-green-200 inline-block mr-1" /> Low (1-4)</span>
          <span className="flex items-center"><span className="w-3 h-3 bg-yellow-200 inline-block mr-1" /> Medium (5-9)</span>
          <span className="flex items-center"><span className="w-3 h-3 bg-orange-200 inline-block mr-1" /> High (10-15)</span>
          <span className="flex items-center"><span className="w-3 h-3 bg-red-200 inline-block mr-1" /> Critical (16-25)</span>
        </div>
      </div>
    </div>
  );
}
