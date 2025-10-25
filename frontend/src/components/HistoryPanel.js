import React from 'react';
import '../styles/HistoryPanel.css';

const HistoryPanel = ({ history, onClose, onSelect }) => {
  return (
    <div className="history-modal">
      <div className="history-container">
        <div className="history-header">
          <h2>Try-On History</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="history-content">
          {history.length === 0 ? (
            <div className="history-empty">
              <p>No history yet. Start by creating your first try-on!</p>
            </div>
          ) : (
            <div className="history-grid">
              {history.map((item, index) => (
                <div 
                  key={index} 
                  className="history-item"
                  onClick={() => {
                    onSelect(item);
                    onClose();
                  }}
                >
                  <div className="history-images">
                    <img src={item.personImage} alt="Person" className="history-thumb" />
                    <div className="history-arrow">→</div>
                    <img src={item.clothingImage} alt="Clothing" className="history-thumb" />
                    <div className="history-arrow">=</div>
                    <img src={item.resultImage} alt="Result" className="history-thumb result" />
                  </div>
                  <div className="history-info">
                    <span className="history-time">
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryPanel;
