import React from 'react';
import '../styles/StatusIndicator.css';

const STATE_LABELS = {
  idle: 'En ligne',
  listening: "À l'écoute",
  thinking: 'Réfléchit…',
  speaking: 'Répond…',
};

/**
 * Indicateur de statut — point de couleur + libellé clair.
 * Volontairement minimal : compréhensible en un coup d'œil,
 * sans code visuel à apprendre.
 */
export default function StatusIndicator({ state = 'idle' }) {
  const label = STATE_LABELS[state] || STATE_LABELS.idle;
  return (
    <div className={`status-indicator state-${state}`}>
      <span className="status-dot" />
      <span className="status-label">{label}</span>
    </div>
  );
}
