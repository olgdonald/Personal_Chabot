import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, RotateCcw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import StatusIndicator from './components/StatusIndicator';
import './styles/ChatbotCV.css';

const STARTERS = [
  { label: "Compétences techniques", prompt: "Parlez-moi des compétences techniques de Jean Donald" },
  { label: "Projets récents", prompt: "Quels sont ses projets les plus récents ?" },
  { label: "Parcours de formation", prompt: "Décrivez son parcours de formation" },
  { label: "Expériences professionnelles", prompt: "Quelles sont ses expériences professionnelles ?" },
];

const GREETING = "Bonjour \uD83D\uDC4B Je suis l'assistant de Jean Donald Olinga. Posez-moi une question sur son parcours, ses compétences ou ses projets.";

const Message = ({ message, isUser }) => (
  <div className={`message-row ${isUser ? 'from-user' : 'from-assistant'}`}>
    <div className={`message-bubble ${isUser ? 'user' : 'bot'}`}>
      {isUser ? (
        message
      ) : (
        <ReactMarkdown>{message}</ReactMarkdown>
      )}
    </div>
  </div>
);

export default function ChatbotCV() {
  const [messages, setMessages] = useState([
    { text: GREETING, isUser: false, id: 1 }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [robotState, setRobotState] = useState('idle');
  const [sessionId, setSessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const conversationStarted = messages.some(m => m.isUser);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const maxHeight = window.innerWidth <= 640 ? 140 : 120;
    const minHeight = window.innerWidth <= 640 ? 44 : 48;
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = `${newHeight}px`;
  }, [inputMessage]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isTyping, scrollToBottom]);

  const sendMessageToAPI = async (message) => {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    const data = await response.json();
    return data.response;
  };

  const handleSendMessage = async () => {
    const trimmed = inputMessage.trim();
    if (trimmed === '' || isTyping) return;

    setMessages(prev => [...prev, { text: trimmed, isUser: true, id: Date.now() }]);
    setInputMessage('');
    setRobotState('thinking');
    setIsTyping(true);
    setError(null);

    try {
      const botResponse = await sendMessageToAPI(trimmed);
      const botMessage = { text: botResponse, isUser: false, id: Date.now() + 1 };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
      setRobotState('speaking');
      setTimeout(() => setRobotState('idle'), 2500);
    } catch (err) {
      console.error("Erreur lors de l'appel API:", err);
      setIsTyping(false);
      setRobotState('idle');
      setError("Une erreur s'est produite. Merci de réessayer.");
      setMessages(prev => [...prev, {
        text: "Je rencontre des difficultés techniques. Veuillez réessayer dans quelques instants.",
        isUser: false,
        id: Date.now() + 1
      }]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleStarterClick = (prompt) => {
    setInputMessage(prompt);
    setRobotState('listening');
    textareaRef.current?.focus();
  };

  const handleNewConversation = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch (err) {
      console.warn('Reset serveur impossible, poursuite en local:', err);
    }
    setMessages([{ text: GREETING, isUser: false, id: Date.now() }]);
    setInputMessage('');
    setError(null);
    setSessionId(Math.random().toString(36).substr(2, 9));
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="monogram">JD</div>
          <div className="header-identity">
            <h1 className="title">Jean Donald Olinga</h1>
            <p className="subtitle">Élève-ingénieur — Intelligence Artificielle</p>
          </div>
          <StatusIndicator state={robotState} />
          {conversationStarted && (
            <button
              className="reset-button"
              onClick={handleNewConversation}
              aria-label="Nouvelle conversation"
              title="Nouvelle conversation"
            >
              <RotateCcw size={16} />
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <div className="error-inner">
            <span>{error}</span>
            <button onClick={() => setError(null)} aria-label="Fermer">✕</button>
          </div>
        </div>
      )}

      <main className={`app-main ${!conversationStarted ? 'is-empty' : ''}`}>
        <div className="messages-container">
          {messages.map(m => <Message key={m.id} message={m.text} isUser={m.isUser} />)}

          {!conversationStarted && !isTyping && (
            <div className="starter-grid">
              {STARTERS.map((s, i) => (
                <button
                  key={i}
                  className="starter-card"
                  onClick={() => handleStarterClick(s.prompt)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}

          {isTyping && (
            <div className="message-row from-assistant">
              <div className="message-bubble bot">
                <div className="typing-indicator">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <div className="app-input-bar">
        <div className="input-inner">
          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => {
                  setInputMessage(e.target.value);
                  setRobotState(e.target.value.trim() !== '' ? 'listening' : 'idle');
                }}
                onKeyDown={handleKeyDown}
                placeholder="Écrivez votre question ici…"
                disabled={isTyping}
                rows="1"
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={isTyping || inputMessage.trim() === ''}
              className="send-button"
              aria-label="Envoyer le message"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="footnote">Réponses générées automatiquement à partir du profil de Jean Donald Olinga.</p>
        </div>
      </div>
    </div>
  );
}
