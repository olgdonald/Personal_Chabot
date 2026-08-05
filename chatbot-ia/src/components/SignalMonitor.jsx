import React from 'react';
import '../styles/SignalMonitor.css';

// Étiquettes affichées selon l'état de l'assistant.
const STATE_LABELS = {
  idle: 'EN LIGNE',
  listening: 'ÉCOUTE',
  thinking: 'RÉFLEXION',
  speaking: 'RÉPONSE',
};

/**
 * Moniteur de signal — signature visuelle du dossier.
 * Remplace un avatar illustratif par un instrument de mesure
 * (façon oscilloscope) qui traduit visuellement l'état de
 * l'assistant : au repos, à l'écoute, en réflexion, en réponse.
 */
export default function SignalMonitor({ state = 'idle' }) {
  const label = STATE_LABELS[state] || STATE_LABELS.idle;
  const bars = Array.from({ length: 7 });

  return (
    <div className={`signal-monitor state-${state}`} role="status" aria-label={`Assistant : ${label.toLowerCase()}`}>
      <span className="signal-dot" />
      <div className="signal-bars" aria-hidden="true">
        {bars.map((_, i) => (
          <span key={i} className="signal-bar" style={{ animationDelay: `${i * 0.09}s` }} />
        ))}
      </div>
      <span className="signal-label">{label}</span>
    </div>
  );
}
