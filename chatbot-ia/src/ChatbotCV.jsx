import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Minimize2, Maximize2 } from 'lucide-react';
import FloatingRobot from './components/FloatingRobot';
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
    <div className={`message-wrapper ${isUser ? 'user' : ''}`}>
      <div className={`message-content ${isUser ? 'user' : ''}`}>
        <div className={`avatar ${isUser ? 'user' : 'bot'}`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        <div className={`message-bubble ${isUser ? 'user' : 'bot'}`}>
          {displayedText}
          {!isUser && currentIndex < message.length && <span className="cursor"></span>}
        </div>
      </div>
    </div>
  );
};

export default function ChatbotCV() {
  const [messages, setMessages] = useState([
    { text: "Bonjour ! Je suis l'assistant personnel de Jean Donald Olinga. Posez-moi des questions sur son parcours, ses compétences ou ses projets !", isUser: false, id: 1 }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [robotState, setRobotState] = useState('idle');
  const [isMinimized, setIsMinimized] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const [error, setError] = useState(null);
  const [textareaHeight, setTextareaHeight] = useState('44px');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Configuration de l'API (à adapter selon votre déploiement)
  // const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Fonction pour ajuster automatiquement la hauteur
  const adjustTextareaHeight = (textarea) => {
    if (!textarea) return;
    
    // Reset height to get accurate scrollHeight
    textarea.style.height = 'auto';
    const maxHeight = window.innerWidth <= 768 ? 140 : 120; // Plus haut sur mobile
    const minHeight = window.innerWidth <= 768 ? 44 : 48;
    
    let newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = newHeight + 'px';
    setTextareaHeight(newHeight + 'px');
    
    // Ajouter classe pour animation container si nécessaire
    const inputArea = document.querySelector('.input-area');
    if (newHeight > minHeight + 10) {
      inputArea?.classList.add('expanded');
    } else {
      inputArea?.classList.remove('expanded');
    }
  };

  // Ajouter une fonction pour reset la hauteur après envoi
  const resetTextareaHeight = () => {
    const textarea = document.querySelector('.input-wrapper textarea');
    if (textarea) {
      const minHeight = window.innerWidth <= 768 ? 44 : 48;
      textarea.style.height = minHeight + 'px';
      setTextareaHeight(minHeight + 'px');
      
      // Retirer classe expanded
      const inputArea = document.querySelector('.input-area');
      inputArea?.classList.remove('expanded');
    }
  };

  const sendMessageToAPI = async (message) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        }),
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

  // Modifier handleSendMessage pour reset la hauteur
  const handleSendMessage = async () => {
    if (inputMessage.trim() === '' || isTyping) return;

    const userMessage = { text: inputMessage, isUser: true, id: Date.now() };
    const messageToSend = inputMessage;
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    
    // Reset la hauteur du textarea
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
      }, 1000); // Délai pour simuler la réflexion

    } catch (error) {
      setIsTyping(false);
      setRobotState('idle');
      setError('Désolé, une erreur s\'est produite. Veuillez réessayer.');
      
      const errorMessage = {
        text: "Désolé, je rencontre des difficultés techniques. Veuillez réessayer dans quelques instants.",
        isUser: false,
        id: Date.now() + 1
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    // Remettre les suggestions après envoi
    setTimeout(() => {
      const suggestionsEl = document.querySelector('.suggestions');
      if (suggestionsEl) {
        suggestionsEl.classList.remove('typing');
      }
    }, 100);
  };

  // Modifier handleInputChange
  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    setRobotState(e.target.value.trim() !== '' ? 'listening' : 'idle');
    
    // Ajuster la hauteur automatiquement
    adjustTextareaHeight(e.target);
    
    // Gérer l'affichage des suggestions
    const suggestionsEl = document.querySelector('.suggestions');
    if (suggestionsEl) {
      if (e.target.value.trim() !== '') {
        suggestionsEl.classList.add('typing');
      } else {
        suggestionsEl.classList.remove('typing');
      }
    }
  };

  const handleKeyPress = (e) => { 
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(); 
    }
  };

  const handleRobotClick = () => {
    console.log('Robot cliqué !');
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    setRobotState('listening');
  };

  const resetConversation = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId
        }),
      });
      
      setMessages([
        { text: "Bonjour ! Je suis l'assistant personnel de Jean Donald Olinga. Posez-moi des questions sur son parcours, ses compétences ou ses projets !", isUser: false, id: Date.now() }
      ]);
      setError(null);
    } catch (error) {
      console.error('Erreur lors de la réinitialisation:', error);
    }
  };

  // Ajouter un useEffect pour gérer le resize de fenêtre
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
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <FloatingRobot 
              state={robotState} 
              onInteraction={handleRobotClick}
            />
            <div>
              <h1 className="title">Assistant CV Intelligent</h1>
              <p className="subtitle">Découvrez le profil de Jean Donald Olinga de manière interactive</p>
            </div>
          </div>
          {/* <div className="header-actions">
            <button 
              onClick={resetConversation} 
              className="reset-button"
              title="Nouvelle conversation"
            >
              🔄
            </button>
          </div> */}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div className="chat-container" style={{ height: isMinimized ? '20px' : undefined, overflow: isMinimized ? 'hidden' : 'visible' }}>
        <div className="messages-area">
          <div className="messages-container">
            {messages.map(m => <Message key={m.id} message={m.text} isUser={m.isUser} />)}
            {isTyping && (
              <div className="message-wrapper">
                <div className="message-content">
                  <div className="avatar bot"><Bot size={16} /></div>
                  <div className="message-bubble bot">
                    <div className="typing-indicator">
                      {[0,1,2].map(i => <div key={i} className="typing-dot" style={{animationDelay:`${i*0.2}s`}}></div>)}
                    </div>
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
                  <textarea 
                    value={inputMessage} 
                    onChange={handleInputChange} 
                    onKeyPress={handleKeyPress} 
                    placeholder="Posez-moi une question sur le CV de Jean Donald..." 
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
                >
                  <Send size={20} />
                </button>
              </div>
            </div>
          )}
        </div>

        {!isMinimized && (
          <div className="suggestions">
            <div className="suggestions-container">
              {[
                "Parlez-moi des compétences techniques de Jean Donald",
                "Quels sont ses projets les plus récents ?",
                "Décrivez son parcours de formation",
                "Quelles sont ses expériences professionnelles ?"
              ].map((s,i) => (
                <button 
                  key={i} 
                  onClick={() => handleSuggestionClick(s)} 
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
  );
}