import React, { useState, useEffect } from 'react';
import { Bot, Key, Cpu, X, Check, Server } from 'lucide-react';

export default function AISettingsModal({ isOpen, onClose, onSave, currentSettings }) {
  const [provider, setProvider] = useState(currentSettings?.provider || 'auto');
  const [apiKey, setApiKey] = useState(currentSettings?.apiKey || '');
  const [modelName, setModelName] = useState(currentSettings?.modelName || 'gemini-2.0-flash');
  const [baseUrl, setBaseUrl] = useState(currentSettings?.baseUrl || '');

  const providerDefaults = {
    ollama: { defaultModel: 'llama3', defaultUrl: 'http://localhost:11434/v1', requiresKey: false },
    gemini: { defaultModel: 'gemini-2.0-flash', defaultUrl: '', requiresKey: true },
    groq: { defaultModel: 'llama-3.3-70b-versatile', defaultUrl: '', requiresKey: true },
    openai: { defaultModel: 'gpt-4o-mini', defaultUrl: '', requiresKey: true },
    auto: { defaultModel: 'gemini-2.0-flash', defaultUrl: '', requiresKey: false }
  };

  const handleProviderChange = (e) => {
    const selected = e.target.value;
    setProvider(selected);
    const defaults = providerDefaults[selected] || providerDefaults.auto;
    setModelName(defaults.defaultModel);
    setBaseUrl(defaults.defaultUrl);
  };

  const handleSave = () => {
    onSave({
      provider,
      apiKey,
      modelName,
      baseUrl
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '520px', background: '#12161f' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bot size={24} color="#a855f7" />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>AI Provider & BYOK Settings</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Provider Selection */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#9ca3af', marginBottom: '6px' }}>
              Select AI Provider (Bring Your Own Key)
            </label>
            <select className="form-select" value={provider} onChange={handleProviderChange}>
              <option value="auto">Auto-Detect / Offline Fallback</option>
              <option value="ollama">Ollama (Local / 100% Free - No API Key)</option>
              <option value="gemini">Google Gemini (Recommended Cloud)</option>
              <option value="groq">Groq (Ultra-Fast Inference)</option>
              <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
            </select>
          </div>

          {/* API Key Input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#9ca3af', marginBottom: '6px' }}>
              API Key {providerDefaults[provider]?.requiresKey ? '(Required)' : '(Optional)'}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                className="form-input"
                placeholder={provider === 'ollama' ? 'No API key needed for local Ollama' : 'Paste API Key (sk-...)'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={provider === 'ollama'}
              />
              <Key size={16} style={{ position: 'absolute', right: '12px', top: '12px', color: '#6b7280' }} />
            </div>
          </div>

          {/* Model Name Selection / Custom Input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#9ca3af', marginBottom: '6px' }}>
              Select or Type Custom Model Name
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. gemini-2.0-flash, llama-3.3-70b-versatile, gpt-4o-mini"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
            />
          </div>

          {/* Custom Base URL (for Ollama or Local proxy) */}
          {provider === 'ollama' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#9ca3af', marginBottom: '6px' }}>
                Ollama Base Endpoint URL
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="http://localhost:11434/v1"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
              />
            </div>
          )}
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>
            <Check size={16} /> Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
