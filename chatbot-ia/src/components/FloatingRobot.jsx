import React, { useState, useEffect } from 'react';
import '../styles/FloatingRobot.css';

const FloatingRobot = ({ state = 'idle', onInteraction }) => {
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  // Animation des yeux qui suivent la souris
  useEffect(() => {
    const handleMouseMove = (e) => {
      const robot = document.querySelector('.floating-robot');
      if (robot && isHovered) {
        const rect = robot.getBoundingClientRect();
        const robotCenterX = rect.left + rect.width / 2;
        const robotCenterY = rect.top + rect.height / 2;
        
        const deltaX = e.clientX - robotCenterX;
        const deltaY = e.clientY - robotCenterY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        const maxMove = 2;
        const moveX = Math.max(-maxMove, Math.min(maxMove, (deltaX / distance) * maxMove * Math.min(distance / 100, 1)));
        const moveY = Math.max(-maxMove, Math.min(maxMove, (deltaY / distance) * maxMove * Math.min(distance / 100, 1)));
        
        setEyePosition({ x: moveX || 0, y: moveY || 0 });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [isHovered]);

  const getStateClass = () => {
    switch (state) {
      case 'thinking': return 'thinking';
      case 'speaking': return 'speaking';
      case 'listening': return 'listening';
      default: return 'idle';
    }
  };

  return (
    <div 
      className={`floating-robot ${getStateClass()}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onInteraction}
    >
      {/* Corps principal */}
      <div className="robot-body">
        
        {/* Tête */}
        <div className="robot-head">
          {/* Yeux */}
          <div className="eyes">
            <div className="eye">
              <div 
                className="pupil"
                style={{
                  transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)`
                }}
              />
            </div>
            <div className="eye">
              <div 
                className="pupil"
                style={{
                  transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)`
                }}
              />
            </div>
          </div>
          
          {/* Bouche */}
          <div className="mouth" />
        </div>
        
        {/* Corps */}
        <div className="robot-torso">
          <div className="status-light" />
        </div>
      </div>
    </div>
  );
};

export default FloatingRobot;