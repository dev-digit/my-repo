import React, { useState, useEffect } from 'react';
import ChatInterface from './ChatInterface';
import ModeSelector from './ModeSelector';
import { apiClient } from './api/client';
import './App.css';

function App() {
  const [modes, setModes] = useState([]);
  const [models, setModels] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);

      // Load modes
      const modesResponse = await apiClient.get('/api/v1/modes/');
      setModes(modesResponse.data.data.modes || []);

      // Load available models
      const modelsResponse = await apiClient.get('/api/v1/chat/stats');
      setModels(modelsResponse.data.data?.models || []);

      // Check health
      const healthResponse = await apiClient.get('/api/v1/health/detailed');
      setHealth(healthResponse.data);

    } catch (err) {
      console.error('Failed to initialize app:', err);
      setError('Failed to connect to Pombi API. Make sure the backend is running on localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <h2>Initializing Pombi AI Assistant...</h2>
          <p>Connecting to the AI engine and loading available modes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="App">
        <div className="error-container">
          <h2>Connection Error</h2>
          <p>{error}</p>
          <button onClick={initializeApp} className="retry-button">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo">
            <h1>🤖 Pombi AI Assistant</h1>
            <span className="tagline">Advanced Conversational AI</span>
          </div>
          <div className="status-indicators">
            {health && (
              <div className={`status ${health.status}`}>
                <span className="status-dot"></span>
                {health.status.toUpperCase()}
              </div>
            )}
            <div className="model-count">
              {models.length} models available
            </div>
          </div>
        </div>
      </header>

      <main className="App-main">
        <div className="container">
          <div className="sidebar">
            <ModeSelector modes={modes} />
            <div className="system-info">
              <h3>System Information</h3>
              {health && (
                <div className="health-info">
                  <div className="info-item">
                    <span>Status:</span>
                    <span className={health.status}>{health.status}</span>
                  </div>
                  <div className="info-item">
                    <span>Version:</span>
                    <span>{health.version}</span>
                  </div>
                  {health.components && (
                    <div className="info-item">
                      <span>Models:</span>
                      <span>
                        {Object.values(health.components.models || {}).filter(Boolean).length} healthy
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="chat-section">
            <ChatInterface modes={modes} />
          </div>
        </div>
      </main>

      <footer className="App-footer">
        <p>
          Pombi AI Assistant - Testing Interface |
          <a href="/docs" target="_blank" rel="noopener noreferrer">
            API Documentation
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;