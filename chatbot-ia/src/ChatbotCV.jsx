import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import SignalMonitor from './components/SignalMonitor';
import './styles/ChatbotCV.css';

const Message = ({ message, isUser, isTyping = false }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (!isUser && !isTyping) {
      const timer = setTimeout(() => {
        if (currentIndex < message.length) {
          setDisplayedText(message.slice(0, currentIndex + 1));
          setCurrentIndex(currentIndex + 1);
        }
      }, 30);
      return () => clearTimeout(timer);
    } else {
      setDisplayedText(message);
    }
  }, [message, currentIndex, isUser, isTyping]);

  return (
    <div className={`message-row ${isUser ? 'from-user' : 'from-assistant'}`}>
      <span className="message-tag">{isUser ? 'VOUS' : 'IA · JDO'}</span>
      <div className={`message-bubble ${isUser ? 'user' : 'bot'}`}>
        {displayedText}
        {!isUser && currentIndex < message.length && <span className="cursor" />}
      </div>
    </div>
  );
};

export default function ChatbotCV() {
  const [messages, setMessages] = useState([
    { text: "Bonjour. Je suis l'assistant de profil de Jean Donald Olinga — posez-moi une question sur son parcours, ses compétences ou ses projets.", isUser: false, id: 1 }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [robotState, setRobotState] = useState('idle');
  const [isMinimized] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const [error, setError] = useState(null);
  const [textareaHeight, setTextareaHeight] = useState('44px');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const adjustTextareaHeight = (textarea) => {
    if (!textarea) return;
    textarea.style.height = 'auto';
    const maxHeight = window.innerWidth <= 768 ? 140 : 120;
    const minHeight = window.innerWidth <= 768 ? 44 : 48;

    let newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = newHeight + 'px';
    setTextareaHeight(newHeight + 'px');

    const inputArea = document.querySelector('.input-area');
    if (newHeight > minHeight + 10) {
      inputArea?.classList.add('expanded');
    } else {
      inputArea?.classList.remove('expanded');
    }
  };

  const resetTextareaHeight = () => {
    const textarea = document.querySelector('.input-wrapper textarea');
    if (textarea) {
      const minHeight = window.innerWidth <= 768 ? 44 : 48;
      textarea.style.height = minHeight + 'px';
      setTextareaHeight(minHeight + 'px');
      document.querySelector('.input-area')?.classList.remove('expanded');
    }
  };

  const sendMessageToAPI = async (message) => {
    try {
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
    } catch (error) {
      console.error('Erreur lors de l\'appel API:', error);
      throw error;
    }
  };

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '' || isTyping) return;

    const userMessage = { text: inputMessage, isUser: true, id: Date.now() };
    const messageToSend = inputMessage;

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    resetTextareaHeight();

    setRobotState('thinking');
    setIsTyping(true);
    setError(null);

    try {
      const botResponse = await sendMessageToAPI(messageToSend);

      setTimeout(() => {
        const botMessage = { text: botResponse, isUser: false, id: Date.now() + 1 };
        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
        setRobotState('speaking');

        setTimeout(() => { setRobotState('idle'); }, 3000);
      }, 1000);

    } catch (error) {
      setIsTyping(false);
      setRobotState('idle');
      setError('Une erreur s\'est produite. Merci de réessayer.');

      const errorMessage = {
        text: "Je rencontre des difficultés techniques. Veuillez réessayer dans quelques instants.",
        isUser: false,
        id: Date.now() + 1
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setTimeout(() => {
      document.querySelector('.suggestions')?.classList.remove('typing');
    }, 100);
  };

  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    setRobotState(e.target.value.trim() !== '' ? 'listening' : 'idle');
    adjustTextareaHeight(e.target);

    const suggestionsEl = document.querySelector('.suggestions');
    if (suggestionsEl) {
      suggestionsEl.classList.toggle('typing', e.target.value.trim() !== '');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    setRobotState('listening');
  };

  useEffect(() => {
    const handleResize = () => {
      const textarea = document.querySelector('.input-wrapper textarea');
      if (textarea && inputMessage) {
        adjustTextareaHeight(textarea);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [inputMessage]);

  return (
    <div className="chatbot-wrapper">
      <div className="grid-backdrop" aria-hidden="true" />

      <div className="dossier">
        <header className="header">
          <div className="header-content">
            <div className="header-identity">
              <span className="eyebrow">Dossier technique — réf. JDO/2026</span>
              <h1 className="title">Jean Donald Olinga</h1>
              <p className="subtitle">Assistant de profil — élève-ingénieur, spécialisation Intelligence Artificielle</p>
            </div>
            <SignalMonitor state={robotState} />
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)} aria-label="Fermer">✕</button>
          </div>
        )}

        <div className="chat-container" style={{ height: isMinimized ? '20px' : undefined, overflow: isMinimized ? 'hidden' : 'visible' }}>
          <div className="messages-area">
            <div className="messages-container">
              {messages.map(m => <Message key={m.id} message={m.text} isUser={m.isUser} />)}
              {isTyping && (
                <div className="message-row from-assistant">
                  <span className="message-tag">IA · JDO</span>
                  <div className="message-bubble bot">
                    <div className="typing-indicator">
                      {[0, 1, 2].map(i => <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }}></div>)}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {!isMinimized && (
              <div className="input-area">
                <div className="input-container">
                  <div className="input-wrapper">
                    <span className="prompt-glyph" aria-hidden="true">›</span>
                    <textarea
                      value={inputMessage}
                      onChange={handleInputChange}
                      onKeyPress={handleKeyPress}
                      placeholder="Posez une question sur le profil de Jean Donald…"
                      disabled={isTyping}
                      rows="1"
                      style={{
                        resize: 'none',
                        height: textareaHeight,
                        minHeight: window.innerWidth <= 768 ? '44px' : '48px'
                      }}
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
              </div>
            )}
          </div>

          {!isMinimized && (
            <div className="suggestions">
              <div className="suggestions-container">
                {[
                  "Compétences techniques",
                  "Projets récents",
                  "Parcours de formation",
                  "Expériences professionnelles"
                ].map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(
                      [
                        "Parlez-moi des compétences techniques de Jean Donald",
                        "Quels sont ses projets les plus récents ?",
                        "Décrivez son parcours de formation",
                        "Quelles sont ses expériences professionnelles ?"
                      ][i]
                    )}
                    className="suggestion"
                    disabled={isTyping}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
