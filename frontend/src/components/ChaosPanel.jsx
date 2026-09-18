import React, { useState, useEffect } from 'react';
import { Flame, Plus, Trash2, AlertTriangle, Clock, Zap } from 'lucide-react';

export default function ChaosPanel({ activeProjectId }) {
  const [rules, setRules] = useState([]);
  const [endpointPath, setEndpointPath] = useState('/payments');
  const [httpMethod, setHttpMethod] = useState('*');
  const [failureType, setFailureType] = useState('status_code');
  const [probability, setProbability] = useState(1.0);
  const [statusCode, setStatusCode] = useState(500);
  const [durationMs, setDurationMs] = useState(500);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchRules = async () => {
    if (!activeProjectId) return;
    try {
      const res = await fetch(`/api/v1/chaos/${activeProjectId}/rules`);
      if (res.ok) {
        const data = await res.json();
        setRules(data);
      }
    } catch (err) {
      console.error('Failed to fetch chaos rules', err);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [activeProjectId]);

  const handleAddRule = async () => {
    if (!activeProjectId) return;
    setIsSubmitting(true);

    const config = failureType === 'latency' 
      ? { duration_ms: Number(durationMs) }
      : failureType === 'status_code'
      ? { status_code: Number(statusCode), message: `Chaos Injected ${statusCode} Error` }
      : { payload: '{ "corrupted": [unclosed_json... }' };

    try {
      const res = await fetch(`/api/v1/chaos/${activeProjectId}/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint_path: endpointPath,
          http_method: httpMethod,
          failure_type: failureType,
          probability: Number(probability),
          config: config,
          is_active: true
        })
      });

      if (res.ok) {
        fetchRules();
      }
    } catch (err) {
      console.error('Failed to add chaos rule', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      const res = await fetch(`/api/v1/chaos/${activeProjectId}/rules/${ruleId}`, { method: 'DELETE' });
      if (res.ok) {
        fetchRules();
      }
    } catch (err) {
      console.error('Failed to delete chaos rule', err);
    }
  };

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Flame size={20} color="#f43f5e" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Chaos & Fault Injection Control Center</h3>
        </div>
        <span style={{ fontSize: '0.8rem', color: '#f87171', background: 'rgba(244, 63, 94, 0.15)', padding: '2px 8px', borderRadius: '12px' }}>
          {rules.length} Active Rules
        </span>
      </div>

      {/* Add New Chaos Rule Form */}
      <div style={{ background: '#0d111a', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '14px', marginBottom: '18px' }}>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#9ca3af', marginBottom: '12px' }}>
          Inject New Chaos Rule
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px 140px 100px auto', gap: '10px', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Endpoint Path</label>
            <input type="text" className="form-input" value={endpointPath} onChange={(e) => setEndpointPath(e.target.value)} placeholder="/payments" />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Method</label>
            <select className="form-select" value={httpMethod} onChange={(e) => setHttpMethod(e.target.value)}>
              <option value="*">ANY (*)</option>
              <option value="POST">POST</option>
              <option value="GET">GET</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Failure Mode</label>
            <select className="form-select" value={failureType} onChange={(e) => setFailureType(e.target.value)}>
              <option value="status_code">Error Status</option>
              <option value="latency">Latency Spike</option>
              <option value="malformed">Malformed JSON</option>
            </select>
          </div>

          {failureType === 'status_code' && (
            <div>
              <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Status Code</label>
              <select className="form-select" value={statusCode} onChange={(e) => setStatusCode(e.target.value)}>
                <option value="500">500 Server Error</option>
                <option value="429">429 Rate Limit</option>
                <option value="503">503 Unavailable</option>
                <option value="400">400 Bad Request</option>
              </select>
            </div>
          )}

          {failureType === 'latency' && (
            <div>
              <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Delay (ms)</label>
              <input type="number" className="form-input" value={durationMs} onChange={(e) => setDurationMs(e.target.value)} placeholder="500" />
            </div>
          )}

          {failureType === 'malformed' && (
            <div>
              <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Probability</label>
              <input type="number" step="0.1" max="1.0" min="0.1" className="form-input" value={probability} onChange={(e) => setProbability(e.target.value)} />
            </div>
          )}

          <button className="btn-primary" onClick={handleAddRule} disabled={isSubmitting} style={{ background: '#f43f5e' }}>
            <Plus size={16} /> Inject Rule
          </button>
        </div>
      </div>

      {/* Active Rules List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {rules.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: '#6b7280', textAlign: 'center', padding: '16px' }}>No active chaos rules. All endpoints behaving normally.</p>
        ) : (
          rules.map((rule) => (
            <div key={rule.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: '#090d16', border: '1px solid rgba(244, 63, 94, 0.2)',
              borderRadius: '8px', padding: '10px 14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AlertTriangle size={16} color="#f43f5e" />
                <span className="badge-method badge-post" style={{ background: 'rgba(244,63,94,0.15)', color: '#f87171' }}>
                  {rule.http_method}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#e5e7eb' }}>
                  {rule.endpoint_path}
                </span>
                <span style={{ fontSize: '0.78rem', color: '#9ca3af' }}>
                  → Mode: <strong>{rule.failure_type}</strong> ({rule.failure_type === 'status_code' ? `HTTP ${rule.config.status_code}` : `${rule.config.duration_ms || 500}ms delay`})
                </span>
              </div>

              <button onClick={() => handleDeleteRule(rule.id)} style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer' }} title="Delete Rule">
                <Trash2 size={16} color="#f87171" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
