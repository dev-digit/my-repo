import React, { useState, useEffect } from 'react';
import { apiClient } from './api/client';
import './ModeSelector.css';

function ModeSelector({ modes, onModeChange, selectedMode }) {
  const [modeExamples, setModeExamples] = useState(null);
  const [loadingExamples, setLoadingExamples] = useState(false);
  const [expandedMode, setExpandedMode] = useState(null);

  useEffect(() => {
    if (selectedMode) {
      loadModeExamples(selectedMode);
    }
  }, [selectedMode]);

  const loadModeExamples = async (modeName) => {
    try {
      setLoadingExamples(true);
      const response = await apiClient.get(`/api/v1/modes/examples/${modeName}`);
      setModeExamples(response.data.data);
      setExpandedMode(modeName);
    } catch (error) {
      console.error('Failed to load mode examples:', error);
    } finally {
      setLoadingExamples(false);
    }
  };

  const handleModeClick = (modeName) => {
    if (onModeChange) {
      onModeChange(modeName);
    }
    loadModeExamples(modeName);
  };

  return (
    <div className="mode-selector">
      <h3>Conversation Modes</h3>
      <div className="modes-list">
        {modes.map((mode) => (
          <div
            key={mode.name}
            className={`mode-item ${selectedMode === mode.name ? 'selected' : ''}`}
            onClick={() => handleModeClick(mode.name)}
          >
            <div className="mode-header">
              <div className="mode-icon">
                {mode.name === 'creative' && '🎨'}
                {mode.name === 'precise' && '🎯'}
                {mode.name === 'teach' && '📚'}
                {mode.name === 'code' && '💻'}
                {mode.name === 'analyze' && '📊'}
              </div>
              <div className="mode-info">
                <h4>{mode.name.charAt(0).toUpperCase() + mode.name.slice(1)}</h4>
                <p>{mode.description}</p>
              </div>
            </div>

            {expandedMode === mode.name && modeExamples && (
              <div className="mode-examples">
                {loadingExamples ? (
                  <div className="loading-examples">Loading examples...</div>
                ) : (
                  <div>
                    <p className="examples-description">{modeExamples.description}</p>
                    <div className="example-prompts">
                      <h5>Example prompts:</h5>
                      {modeExamples.prompts.slice(0, 3).map((prompt, index) => (
                        <div key={index} className="example-prompt">
                          "{prompt}"
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ModeSelector;