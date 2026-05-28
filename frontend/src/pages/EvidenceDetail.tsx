import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getEvidence } from '../lib/api';

interface Evidence {
  id: string;
  framework_control_id: string;
  collector_type: string;
  collector_version: string;
  raw_data: any;
  structured_result: any;
  is_passing: boolean;
  pass_fail_reason: string;
  collected_at: string;
}

export default function EvidenceDetail() {
  const { id } = useParams<{ id: string }>();
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getEvidence(id)
      .then(setEvidence)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-center py-12">Loading...</div>;
  if (!evidence) return <div className="text-center py-12">Evidence not found</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Evidence Detail</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Raw Data</h2>
            <pre className="bg-gray-50 p-4 rounded overflow-auto max-h-96 text-xs font-mono">
              {JSON.stringify(evidence.raw_data, null, 2)}
            </pre>
          </div>

          {evidence.structured_result && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Structured Result</h2>
              <pre className="bg-gray-50 p-4 rounded overflow-auto max-h-64 text-xs font-mono">
                {JSON.stringify(evidence.structured_result, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Metadata</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Collector</dt>
                <dd className="font-mono">{evidence.collector_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Version</dt>
                <dd>{evidence.collector_version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Result</dt>
                <dd className={evidence.is_passing ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                  {evidence.is_passing ? 'PASS' : 'FAIL'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Collected</dt>
                <dd>{evidence.collected_at ? new Date(evidence.collected_at).toLocaleString() : ''}</dd>
              </div>
            </dl>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Reason</h2>
            <p className="text-sm text-gray-700">{evidence.pass_fail_reason}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
