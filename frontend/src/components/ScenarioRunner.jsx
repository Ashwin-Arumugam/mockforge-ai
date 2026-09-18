import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, CheckCircle2, Play, AlertCircle, RefreshCw } from 'lucide-react';

export default function ScenarioRunner({ activeProjectId, aiSettings }) {
  const [scenarios, setScenarios] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSummary, setAnalysisSummary] = useState(null);
  const [activeTab, setActiveTab] = useState('scenarios');

  const fetchScenarios = async () => {
    if (!activeProjectId) return;
    try {
      const res = await fetch(`/api/v1/agents/${activeProjectId}/scenarios`);
      if (res.ok) {
        const data = await res.json();
        setScenarios(data);
      }
    } catch (err) {
      console.error('Failed to fetch scenarios', err);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, [activeProjectId]);

  const handleRunAgentAnalysis = async () => {
    if (!activeProjectId) return;
    setIsAnalyzing(true);
    setAnalysisSummary(null);

    try {
      const res = await fetch(`/api/v1/agents/${activeProjectId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: aiSettings?.provider || 'auto',
          api_key: aiSettings?.apiKey || null,
          model_name: aiSettings?.modelName || null,
          base_url: aiSettings?.baseUrl || null
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Agent analysis failed');
      }

      setAnalysisSummary(data);
      fetchScenarios();
    } catch (err) {
      console.error('Agent analysis error', err);
      setAnalysisSummary({ error: err.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Bot size={20} color="#a855f7" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Multi-Agent AI Compiler & Integration Test Runner</h3>
        </div>

        <button className="btn-primary" onClick={handleRunAgentAnalysis} disabled={isAnalyzing} style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)' }}>
          {isAnalyzing ? <RefreshCw size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {isAnalyzing ? 'Running 5-Agent Swarm...' : 'Synthesize AI Test Journeys'}
        </button>
      </div>

      {/* Analysis Summary */}
      {analysisSummary && (
        <div style={{
          background: analysisSummary.error ? 'rgba(244, 63, 94, 0.12)' : 'rgba(168, 85, 247, 0.12)',
          border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '12px', marginBottom: '16px',
          fontSize: '0.85rem', color: analysisSummary.error ? '#f87171' : '#e5e7eb'
        }}>
          {analysisSummary.error ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={16} /> <span>{analysisSummary.error}</span>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#c084fc', marginBottom: '4px' }}>
                <CheckCircle2 size={16} /> 5-Agent Pipeline Execution Complete!
              </div>
              <p style={{ color: '#9ca3af', fontSize: '0.78rem' }}>
                Model: <strong>{analysisSummary.model_used}</strong> ({analysisSummary.provider_used}) | Extracted <strong>{analysisSummary.erd_entities.length} entities</strong>, <strong>{analysisSummary.state_machines_count} state machines</strong>, and generated <strong>{analysisSummary.scenarios_generated} test journeys</strong>.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Scenario Journeys List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {scenarios.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: '#6b7280', textAlign: 'center', padding: '24px' }}>
            No scenarios generated yet. Click "Synthesize AI Test Journeys" to trigger the multi-agent compiler.
          </p>
        ) : (
          scenarios.map((scenario) => (
            <div key={scenario.id} style={{ background: '#090d16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f3f4f6' }}>{scenario.title}</h4>
                <span style={{
                  fontSize: '0.7rem', padding: '2px 8px', borderRadius: '10px', fontWeight: 600,
                  background: scenario.scenario_type === 'HAPPY_PATH' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  color: scenario.scenario_type === 'HAPPY_PATH' ? '#34d399' : '#fbbf24'
                }}>
                  {scenario.scenario_type}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: '12px' }}>{scenario.description}</p>

              {/* Steps Flow */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {scenario.steps && scenario.steps.map((step, sIdx) => (
                  <div key={sIdx} style={{
                    display: 'flex', alignItems: 'center', gap: '10px', background: '#0d111a',
                    padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)'
                  }}>
                    <span style={{ color: '#6b7280', fontWeight: 600 }}>Step {step.step_number}:</span>
                    <span className={`badge-method badge-${step.http_method.toLowerCase()}`} style={{ fontSize: '0.65rem' }}>{step.http_method}</span>
                    <span style={{ color: '#e5e7eb' }}>{step.endpoint_path}</span>
                    <span style={{ marginLeft: 'auto', color: '#9ca3af', fontSize: '0.75rem' }}>Exp Status: {step.expected_status_code}</span>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
