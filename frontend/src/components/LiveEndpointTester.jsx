import React, { useState, useEffect } from 'react';
import { Play, Send, Code, Layers, RefreshCw, UserCheck } from 'lucide-react';

export default function LiveEndpointTester({ activeProjectId, normalizedSpec }) {
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [requestMethod, setRequestMethod] = useState('GET');
  const [requestPath, setRequestPath] = useState('');
  const [requestBody, setRequestBody] = useState('{\n  "name": "Alice",\n  "email": "alice@example.com"\n}');
  const [responseStatus, setResponseStatus] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastCreatedUserId, setLastCreatedUserId] = useState('usr_demo_1');
  const [userList, setUserList] = useState([]);

  const routes = normalizedSpec?.routes || [];

  // Fetch created users list from state database for active project
  const fetchCreatedUsers = async () => {
    if (!activeProjectId) return;
    try {
      const res = await fetch(`/mock/${activeProjectId}/users`);
      if (res.ok) {
        const users = await res.json();
        if (Array.isArray(users) && users.length > 0) {
          setUserList(users);
          // Default to most recently created user if not set
          if (!users.some(u => u.id === lastCreatedUserId)) {
            setLastCreatedUserId(users[users.length - 1].id);
          }
        }
      }
    } catch {
      // Ignore background fetch errors
    }
  };

  useEffect(() => {
    fetchCreatedUsers();
  }, [activeProjectId]);

  const handleUserChange = (newUserId) => {
    setLastCreatedUserId(newUserId);
    if (selectedRoute) {
      const samplePath = selectedRoute.path.replace(/\{[^}]+\}/g, newUserId);
      setRequestPath(samplePath);

      if (['POST', 'PUT', 'PATCH'].includes(selectedRoute.method)) {
        try {
          const parsed = JSON.parse(requestBody);
          if ('user_id' in parsed) {
            parsed.user_id = newUserId;
            setRequestBody(JSON.stringify(parsed, null, 2));
          }
        } catch {
          // Ignore parse error
        }
      }
    }
  };

  const handleSelectRoute = (route) => {
    setSelectedRoute(route);
    setRequestMethod(route.method);
    const samplePath = route.path.replace(/\{[^}]+\}/g, lastCreatedUserId);
    setRequestPath(samplePath);

    if (['POST', 'PUT', 'PATCH'].includes(route.method)) {
      if (route.path.includes('chat/completions')) {
        setRequestBody(JSON.stringify({
          model: "gpt-4o-mini",
          messages: [{ role: "user", content: "Explain GraphRAG architecture" }]
        }, null, 2));
      } else if (route.path.includes('embeddings')) {
        setRequestBody(JSON.stringify({
          input: "Combining Neo4j knowledge graphs with vector embeddings"
        }, null, 2));
      } else if (route.path.includes('agents/execute')) {
        setRequestBody(JSON.stringify({
          user_id: lastCreatedUserId,
          prompt: "Optimize PyTorch ML hyperparameter tuning pipeline",
          agent_type: "coder"
        }, null, 2));
      } else if (route.path.includes('documents')) {
        setRequestBody(JSON.stringify({
          user_id: lastCreatedUserId,
          title: "GraphRAG Notes",
          content: "Vector search combined with graph traversal."
        }, null, 2));
      } else if (route.path.includes('payments')) {
        setRequestBody(JSON.stringify({
          order_id: "order_1",
          amount: 99.99
        }, null, 2));
      } else {
        setRequestBody(JSON.stringify({
          name: "Ashwin Shanmugam",
          email: "ashwin@bits-pilani.ac.in",
          title: "Sample Item",
          total: 99.99
        }, null, 2));
      }
    }
  };

  const handleExecuteRequest = async () => {
    if (!activeProjectId) return;
    setIsLoading(true);
    setResponseStatus(null);
    setResponseData(null);

    const fullUrl = `/mock/${activeProjectId}${requestPath.startsWith('/') ? '' : '/'}${requestPath}`;

    try {
      const options = {
        method: requestMethod,
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${lastCreatedUserId}`
        }
      };

      if (['POST', 'PUT', 'PATCH'].includes(requestMethod) && requestBody.trim()) {
        options.body = requestBody;
      }

      const res = await fetch(fullUrl, options);
      setResponseStatus(res.status);
      const text = await res.text();
      try {
        const jsonObj = JSON.parse(text);
        setResponseData(jsonObj);

        // Auto-capture created user ID & refresh user list if POST /users was executed
        if (res.status < 300 && requestMethod === 'POST' && jsonObj.id && requestPath.includes('users')) {
          setLastCreatedUserId(jsonObj.id);
          fetchCreatedUsers();
        }
      } catch {
        setResponseData(text);
      }
    } catch (err) {
      setResponseStatus(500);
      setResponseData({ error: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Play size={20} color="#10b981" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Interactive Live Endpoint Inspector</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserCheck size={16} color="#60a5fa" />
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Active User:</span>
          <select
            value={lastCreatedUserId}
            onChange={(e) => handleUserChange(e.target.value)}
            style={{
              background: '#1e293b',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: '#60a5fa',
              padding: '4px 10px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {userList.map(u => (
              <option key={u.id} value={u.id}>
                {u.name || u.email || u.id} ({u.id})
              </option>
            ))}
            {!userList.some(u => u.id === lastCreatedUserId) && (
              <option value={lastCreatedUserId}>{lastCreatedUserId}</option>
            )}
          </select>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '16px' }}>
        {/* Route Selector Sidebar */}
        <div style={{ background: '#090d16', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '10px', padding: '10px', maxHeight: '420px', overflowY: 'auto' }}>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 600, marginBottom: '8px', padding: '4px' }}>
            AVAILABLE ENDPOINTS
          </div>
          {routes.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: '#6b7280', padding: '10px' }}>Upload a spec first.</p>
          ) : (
            routes.map((r, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectRoute(r)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '8px', padding: '8px',
                  borderRadius: '6px', cursor: 'pointer', marginBottom: '4px',
                  background: selectedRoute === r ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  border: selectedRoute === r ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent'
                }}
              >
                <span className={`badge-method badge-${r.method.toLowerCase()}`} style={{ fontSize: '0.65rem' }}>
                  {r.method}
                </span>
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: '#e5e7eb', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {r.path}
                </span>
              </div>
            ))
          )}
        </div>

        {/* REST Request Execution Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Request Bar */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              className="form-select"
              style={{ width: '110px', fontWeight: 700 }}
              value={requestMethod}
              onChange={(e) => setRequestMethod(e.target.value)}
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>

            <input
              type="text"
              className="form-input"
              style={{ fontFamily: 'var(--font-mono)' }}
              placeholder="/users or /users/user_1"
              value={requestPath}
              onChange={(e) => setRequestPath(e.target.value)}
            />

            <button className="btn-primary" onClick={handleExecuteRequest} disabled={isLoading}>
              {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />} Execute
            </button>
          </div>

          {/* Request Body if POST/PUT/PATCH */}
          {['POST', 'PUT', 'PATCH'].includes(requestMethod) && (
            <div>
              <label style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Request JSON Body</label>
              <textarea
                className="form-textarea"
                rows={4}
                style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
              />
            </div>
          )}

          {/* Response Inspector */}
          {responseStatus !== null && (
            <div style={{ background: '#080b12', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px', padding: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 600 }}>RESPONSE DATA</span>
                <span style={{
                  fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
                  background: responseStatus < 300 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)',
                  color: responseStatus < 300 ? '#34d399' : '#f87171'
                }}>
                  {responseStatus} {responseStatus < 300 ? 'OK' : 'ERROR'}
                </span>
              </div>
              <pre className="code-block" style={{ maxHeight: '220px' }}>
                {typeof responseData === 'object' ? JSON.stringify(responseData, null, 2) : responseData}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
