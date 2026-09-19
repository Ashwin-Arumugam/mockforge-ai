import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SpecUploader from './components/SpecUploader';
import EntityGraph from './components/EntityGraph';
import LiveEndpointTester from './components/LiveEndpointTester';
import ChaosPanel from './components/ChaosPanel';
import ScenarioRunner from './components/ScenarioRunner';
import AISettingsModal from './components/AISettingsModal';
import NewProjectModal from './components/NewProjectModal';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeSpec, setActiveSpec] = useState(null);
  const [healthStatus, setHealthStatus] = useState('connecting');
  const [isAISettingsOpen, setIsAISettingsOpen] = useState(false);
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
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
      let res = await fetch('/api/v1/projects');
      if (!res.ok) {
        res = await fetch('/api/v1/projects/');
      }
      if (res.ok) {
        let data = await res.json();
        if (data.length === 0) {
          // Auto-initialize a default project so the user is never blocked
          try {
            const createRes = await fetch('/api/v1/projects', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name: 'Default Project', description: 'Stateful Mock Project' })
            });
            if (createRes.ok) {
              const defaultProj = await createRes.json();
              data = [defaultProj];
            }
          } catch (e) {
            console.error('Failed to auto-create default project', e);
          }
        }
        setProjects(data);
        if (data.length > 0) {
          setActiveProjectId(prev => (prev && data.some(p => p.id === prev)) ? prev : data[0].id);
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

  const handleCreateProject = async (name, description = '') => {
    try {
      let res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: description || 'Stateful Mock Project' })
      });
      if (!res.ok) {
        res = await fetch('/api/v1/projects/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, description: description || 'Stateful Mock Project' })
        });
      }
      if (res.ok) {
        const newProj = await res.json();
        setProjects(prev => [...prev, newProj]);
        setActiveProjectId(newProj.id);
        return newProj;
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
        onCreateProject={() => setIsNewProjectModalOpen(true)}
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

      <NewProjectModal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        onCreate={handleCreateProject}
      />

      <AISettingsModal
        isOpen={isAISettingsOpen}
        onClose={() => setIsAISettingsOpen(false)}
        onSave={setAiSettings}
        currentSettings={aiSettings}
      />
    </div>
  );
}
