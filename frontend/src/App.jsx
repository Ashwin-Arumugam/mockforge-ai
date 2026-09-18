import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SpecUploader from './components/SpecUploader';
import EntityGraph from './components/EntityGraph';
import LiveEndpointTester from './components/LiveEndpointTester';
import ChaosPanel from './components/ChaosPanel';
import ScenarioRunner from './components/ScenarioRunner';
import AISettingsModal from './components/AISettingsModal';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeSpec, setActiveSpec] = useState(null);
  const [healthStatus, setHealthStatus] = useState('connecting');
  const [isAISettingsOpen, setIsAISettingsOpen] = useState(false);
  const [aiSettings, setAiSettings] = useState({
    provider: 'auto',
    apiKey: '',
    modelName: 'gemini-2.0-flash',
    baseUrl: ''
  });

  const fetchHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        setHealthStatus('online');
      }
    } catch {
      setHealthStatus('offline');
    }
  };

  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/v1/projects/');
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && !activeProjectId) {
          setActiveProjectId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch projects', err);
    }
  };

  const fetchActiveSpec = async (projId) => {
    if (!projId) return;
    try {
      const res = await fetch(`/api/v1/specs/${projId}/active`);
      if (res.ok) {
        const data = await res.json();
        setActiveSpec(data);
      } else {
        setActiveSpec(null);
      }
    } catch {
      setActiveSpec(null);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchProjects();
  }, []);

  useEffect(() => {
    if (activeProjectId) {
      fetchActiveSpec(activeProjectId);
    }
  }, [activeProjectId]);

  const handleCreateProject = async () => {
    const name = prompt('Enter Project Name:', `Project ${projects.length + 1}`);
    if (!name) return;

    try {
      const res = await fetch('/api/v1/projects/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: 'Stateful Mock Project' })
      });
      if (res.ok) {
        const newProj = await res.json();
        setProjects([...projects, newProj]);
        setActiveProjectId(newProj.id);
      }
    } catch (err) {
      console.error('Failed to create project', err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        projects={projects}
        activeProjectId={activeProjectId}
        onSelectProject={setActiveProjectId}
        onCreateProject={handleCreateProject}
        onOpenAISettings={() => setIsAISettingsOpen(true)}
        healthStatus={healthStatus}
      />

      <main style={{ flex: 1, maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
          {/* Spec Ingestion Section */}
          <SpecUploader
            activeProjectId={activeProjectId}
            onSpecUploaded={() => fetchActiveSpec(activeProjectId)}
          />

          {/* Entity Graph & Schema Discovered */}
          <EntityGraph
            normalizedSpec={activeSpec?.normalized_spec}
            erdGraph={activeSpec?.erd_graph}
          />

          {/* Live Endpoint Tester */}
          <LiveEndpointTester
            activeProjectId={activeProjectId}
            normalizedSpec={activeSpec?.normalized_spec}
          />

          {/* Grid: Chaos Control Panel + Scenario Runner */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(600px, 1fr))', gap: '24px' }}>
            <ChaosPanel activeProjectId={activeProjectId} />
            <ScenarioRunner activeProjectId={activeProjectId} aiSettings={aiSettings} />
          </div>
        </div>
      </main>

      <AISettingsModal
        isOpen={isAISettingsOpen}
        onClose={() => setIsAISettingsOpen(false)}
        onSave={setAiSettings}
        currentSettings={aiSettings}
      />
    </div>
  );
}
