import React from 'react';
import { Database, GitFork, ShieldCheck } from 'lucide-react';

export default function EntityGraph({ normalizedSpec, erdGraph }) {
  if (!normalizedSpec) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', color: '#6b7280', padding: '40px' }}>
        <Database size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
        <p>No active OpenAPI spec uploaded yet. Upload a spec to inspect discovered entities.</p>
      </div>
    );
  }

  const routes = normalizedSpec.routes || [];
  const entities = erdGraph?.entities || Array.from(new Set(routes.map(r => r.entity_type).filter(e => e !== 'default')));
  const relationships = erdGraph?.relationships || [];

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <GitFork size={20} color="#a855f7" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Discovered Entities & Relational Graph</h3>
        </div>
        <span style={{ fontSize: '0.8rem', color: '#a855f7', background: 'rgba(168, 85, 247, 0.15)', padding: '2px 8px', borderRadius: '12px' }}>
          {entities.length} Entities Discovered
        </span>
      </div>

      {/* Entity Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '14px', marginBottom: '20px' }}>
        {entities.map((entity, idx) => {
          const entityRoutes = routes.filter(r => r.entity_type === entity);
          return (
            <div key={idx} style={{
              background: '#0d111a', border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '10px', padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#f3f4f6', textTransform: 'capitalize' }}>
                  {entity}
                </span>
                <Database size={14} color="#6366f1" />
              </div>
              <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '10px' }}>
                {entityRoutes.length} Associated Endpoints
              </p>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {entityRoutes.map((r, rIdx) => (
                  <span key={rIdx} className={`badge-method badge-${r.method.toLowerCase()}`} style={{ fontSize: '0.65rem', padding: '2px 5px' }}>
                    {r.method}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Relationships Section */}
      {relationships.length > 0 && (
        <div style={{ background: '#090d16', borderRadius: '10px', padding: '14px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#9ca3af', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={14} color="#10b981" /> Foreign Key Relationships & Invariants
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {relationships.map((rel, idx) => (
              <div key={idx} style={{
                display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem',
                color: '#e5e7eb', fontFamily: 'var(--font-mono)'
              }}>
                <span style={{ color: '#60a5fa' }}>{rel.parent_entity}</span>
                <span style={{ color: '#6b7280' }}>1 ──── N</span>
                <span style={{ color: '#c084fc' }}>{rel.child_entity}</span>
                <span style={{ color: '#9ca3af', fontSize: '0.75rem' }}>(via {rel.foreign_key})</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
