import React from 'react';
import { Cpu, Settings, Activity, Plus } from 'lucide-react';

export default function Navbar({ projects, activeProjectId, onSelectProject, onCreateProject, onOpenAISettings, healthStatus }) {
  return (
    <nav style={{
      borderBottom: '1px solid var(--border-card)',
      background: 'rgba(10, 12, 16, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky', top: 0, zIndex: 100,
      padding: '12px 24px'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            borderRadius: '10px', width: '36px', height: '36px',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Cpu size={20} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'white', display: 'flex', alignItems: 'center', gap: '6px' }}>
              MockForge <span style={{ color: '#a855f7' }}>AI</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Stateful API Virtualization & Testing Platform</p>
          </div>
        </div>

        {/* Project Selector & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Health Badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            fontSize: '0.8rem', padding: '4px 10px', borderRadius: '20px',
            background: healthStatus === 'online' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: healthStatus === 'online' ? '#34d399' : '#f87171',
            border: '1px solid rgba(255,255,255,0.08)'
          }}>
            <Activity size={12} />
            <span>{healthStatus === 'online' ? 'Engine Online' : 'Connecting...'}</span>
          </div>

          {/* Project Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <select
              className="form-select"
              style={{ width: '200px', fontSize: '0.85rem' }}
              value={activeProjectId || ''}
              onChange={(e) => onSelectProject(e.target.value)}
            >
              <option value="" disabled>Select Project...</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>

            <button className="btn-secondary" style={{ padding: '8px 12px' }} onClick={onCreateProject} title="Create New Project">
              <Plus size={16} /> New
            </button>
          </div>

          {/* AI Config Settings Button */}
          <button className="btn-secondary" style={{ padding: '8px 14px' }} onClick={onOpenAISettings}>
            <Settings size={16} color="#a855f7" /> AI Config
          </button>
        </div>
      </div>
    </nav>
  );
}
