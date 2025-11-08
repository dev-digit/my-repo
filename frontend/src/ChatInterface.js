import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from './api/client';
import './ChatInterface.css';

function ChatInterface({ modes }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [selectedMode, setSelectedMode] = useState('precise');
  const [modelPreference, setModelPreference] = useState('auto');
  const [showMetadata, setShowMetadata] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      mode: selectedMode,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/api/v1/chat/', {
        message: input,
        mode: selectedMode,
        conversation_id: conversationId,
        model_preference: modelPreference,
      });

      const data = response.data.data;

      // Update conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        mode: data.mode_used,
        model: data.model_used,
        timestamp: new Date().toISOString(),
        metadata: data.metadata,
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);
      setError(error.message || 'Failed to send message');

      // Add error message
      const errorMessage = {
        role: 'error',
        content: error.message || 'Sorry, I encountered an error while processing your message.',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    inputRef.current?.focus();
  };

  const retryLastMessage = () => {
    if (messages.length >= 2) {
      const lastUserMessage = messages[messages.length - 2];
      if (lastUserMessage.role === 'user') {
        setInput(lastUserMessage.content);
        // Remove the last error message and user message
        setMessages(prev => prev.slice(0, -2));
        inputRef.current?.focus();
      }
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <h2>Chat with Pombi</h2>
          <span className={`status ${loading ? 'loading' : 'ready'}`}>
            {loading ? 'Thinking...' : 'Ready'}
          </span>
        </div>
        <div className="chat-controls">
          <select
            value={selectedMode}
            onChange={(e) => setSelectedMode(e.target.value)}
            className="mode-selector"
          >
            {modes.map(mode => (
              <option key={mode.name} value={mode.name}>
                {mode.name.charAt(0).toUpperCase() + mode.name.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={modelPreference}
            onChange={(e) => setModelPreference(e.target.value)}
            className="model-selector"
          >
            <option value="auto">Auto Model</option>
            <option value="openai">OpenAI Models</option>
            <option value="local">Local Models</option>
          </select>

          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className={`metadata-toggle ${showMetadata ? 'active' : ''}`}
          >
            Metadata
          </button>

          <button onClick={clearConversation} className="clear-button">
            Clear
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>👋 Welcome to Pombi AI Assistant!</h3>
            <p>I'm here to help you with a variety of tasks. Choose a mode and start chatting!</p>
            <div className="mode-suggestions">
              <div className="suggestion">
                <strong>Creative:</strong> Write stories, generate ideas, explore possibilities
              </div>
              <div className="suggestion">
                <strong>Precise:</strong> Get accurate, factual answers to your questions
              </div>
              <div className="suggestion">
                <strong>Teach:</strong> Learn new concepts step-by-step
              </div>
              <div className="suggestion">
                <strong>Code:</strong> Get help with programming and technical tasks
              </div>
              <div className="suggestion">
                <strong>Analyze:</strong> Break down complex topics and compare options
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-header">
                  <span className="message-role">
                    {message.role === 'user' && '👤 You'}
                    {message.role === 'assistant' && '🤖 Pombi'}
                    {message.role === 'error' && '⚠️ Error'}
                  </span>
                  {message.mode && (
                    <span className="message-mode">{message.mode}</span>
                  )}
                  {message.model && (
                    <span className="message-model">{message.model}</span>
                  )}
                  <span className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
                </div>
                {showMetadata && message.metadata && (
                  <div className="message-metadata">
                    <h4>Metadata</h4>
                    <div className="metadata-grid">
                      <div className="metadata-item">
                        <span>Response Time:</span>
                        <span>{message.metadata.response_time_ms}ms</span>
                      </div>
                      <div className="metadata-item">
                        <span>Tokens Used:</span>
                        <span>{message.metadata.tokens_used}</span>
                      </div>
                      <div className="metadata-item">
                        <span>Confidence:</span>
                        <span>{(message.metadata.confidence_score * 100).toFixed(1)}%</span>
                      </div>
                      {message.metadata.conversation_turn && (
                        <div className="metadata-item">
                          <span>Turn:</span>
                          <span>#{message.metadata.conversation_turn}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="message assistant loading">
                <div className="message-header">
                  <span className="message-role">🤖 Pombi</span>
                  <span className="message-mode">{selectedMode}</span>
                </div>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          {messages.length >= 2 && (
            <button onClick={retryLastMessage} className="retry-button">
              Retry
            </button>
          )}
        </div>
      )}

      <div className="chat-input">
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            className="message-input"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="send-button"
          >
            {loading ? '...' →' : 'Send →'}
          </button>
        </div>
        <div className="input-footer">
          <span className="input-hint">
            Press Enter to send, Shift+Enter for new line
          </span>
          {conversationId && (
            <span className="conversation-id">
              Session: {conversationId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;