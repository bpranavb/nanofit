import React from 'react';
import '../styles/LoadingOverlay.css';

const LoadingOverlay = ({ message }) => {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="magic-ring-container">
          <div className="magic-ring"></div>
          <div className="magic-icon">✨</div>
        </div>
        
        <h2 className="loading-title">Creating Magic...</h2>
        
        <div className="loading-step" key={message}>
          {message}
        </div>
        
        <div className="progress-container">
          <div className="progress-bar"></div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
