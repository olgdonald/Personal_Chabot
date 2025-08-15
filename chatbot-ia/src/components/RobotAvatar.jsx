import React, { useState } from "react";
import "../styles/RobotAvatar.css";


export default function RobotAvatarModern({ state }) {
  return (
    <div className={`robot-avatar-modern ${state}`}>
      <div className="robot-head">
        <div className="eyes">
          <div className="eye left" />
          <div className="eye right" />
        </div>
        <div className="mouth" />
      </div>

      {/* Particules flottantes pour état thinking */}
      {state === "thinking" && (
        <div className="floating-dots">
          {[0, 1, 2].map((i) => (
            <div key={i} className="dot" style={{ animationDelay: `${i * 0.3}s` }} />
          ))}
        </div>
      )}

      {/* Glow pulsé pour speaking */}
      {state === "speaking" && <div className="speaking-glow" />}
    </div>
  );
}
