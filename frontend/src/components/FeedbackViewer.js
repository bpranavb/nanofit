import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/FeedbackViewer.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FeedbackViewer = ({ onClose }) => {
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [selectedDate, setSelectedDate] = useState('all');
  const [showDailyStats, setShowDailyStats] = useState(false);

  useEffect(() => {
    loadFeedback();
  }, []);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/feedback/all`);
      setFeedback(response.data.feedback);
      setDailyStats(response.data.daily_stats || []);
      
      // Calculate statistics
      if (response.data.feedback.length > 0) {
        const ratings = response.data.feedback.map(f => f.rating);
        const avgRating = (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1);
        const ratingCounts = [1, 2, 3, 4, 5].map(star => 
          ratings.filter(r => r === star).length
        );
        
        setStats({
          total: response.data.total,
          average: avgRating,
          distribution: ratingCounts
        });
      }
      
      setError(null);
    } catch (err) {
      console.error('Error loading feedback:', err);
      setError('Failed to load feedback');
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating) => {
    return (
      <div className="stars-display">
        {[1, 2, 3, 4, 5].map((star) => (
          <span key={star} className={star <= rating ? 'star-filled' : 'star-empty'}>
            ★
          </span>
        ))}
      </div>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="feedback-viewer-modal">
      <div className="feedback-viewer-container">
        <div className="viewer-header">
          <h2>Customer Feedback</h2>
          <div className="header-actions">
            <button 
              className="stats-toggle-button"
              onClick={() => setShowDailyStats(!showDailyStats)}
            >
              {showDailyStats ? '📋 View Feedback' : '📊 Daily Statistics'}
            </button>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">Loading feedback...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : feedback.length === 0 ? (
          <div className="empty-state">
            <p>No feedback received yet.</p>
          </div>
        ) : showDailyStats ? (
          /* Daily Statistics View */
          <>
            {/* Statistics Section */}
            {stats && (
              <div className="feedback-stats">
                <div className="stat-card">
                  <div className="stat-label">Total Feedback</div>
                  <div className="stat-value">{stats.total}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Average Rating</div>
                  <div className="stat-value">
                    {stats.average} ★
                  </div>
                </div>
                <div className="stat-card rating-dist">
                  <div className="stat-label">Rating Distribution</div>
                  <div className="distribution-bars">
                    {[5, 4, 3, 2, 1].map((star) => (
                      <div key={star} className="dist-row">
                        <span className="dist-star">{star}★</span>
                        <div className="dist-bar">
                          <div 
                            className="dist-fill"
                            style={{ 
                              width: `${(stats.distribution[star - 1] / stats.total) * 100}%` 
                            }}
                          />
                        </div>
                        <span className="dist-count">{stats.distribution[star - 1]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Daily Statistics */}
            {dailyStats.length > 0 && (
              <div className="daily-stats-section-full">
                <h3>Daily Feedback Count</h3>
                <div className="daily-stats-grid-large">
                  {dailyStats.map((stat) => (
                    <div key={stat.date} className="daily-stat-card-large">
                      <div className="daily-date-large">{stat.date}</div>
                      <div className="daily-count-large">{stat.count}</div>
                      <div className="daily-label">feedback received</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          /* Feedback List View */
          <>
            {/* Quick Stats Summary */}
            <div className="quick-stats">
              <span className="quick-stat">Total: {stats?.total || 0}</span>
              <span className="quick-stat">Average: {stats?.average || 0}★</span>
              <div className="date-filter-inline">
                <label>Filter by date:</label>
                <select 
                  value={selectedDate} 
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="date-select-inline"
                >
                  <option value="all">All Dates</option>
                  {dailyStats.map((stat) => (
                    <option key={stat.date} value={stat.date}>
                      {stat.date} ({stat.count})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Feedback List */}
            <div className="feedback-list">
              {feedback
                .filter(item => selectedDate === 'all' || item.feedback_date === selectedDate)
                .map((item, index) => (
                <div key={index} className="feedback-item-card">
                  <div className="feedback-serial-badge">
                    #{item.serial_number || 'N/A'}
                  </div>
                  
                  {/* Image First - Most Prominent */}
                  {item.result_image && (
                    <div className="feedback-image-main">
                      <img 
                        src={`data:image/png;base64,${item.result_image}`} 
                        alt="Try-on result" 
                      />
                    </div>
                  )}
                  
                  {/* Customer Info and Rating */}
                  <div className="feedback-details">
                    <div className="feedback-customer-header">
                      <div className="customer-name-large">
                        👤 {item.customer_name || 'Anonymous Customer'}
                      </div>
                      <div className="feedback-timestamp">
                        🕐 {formatDate(item.feedback_timestamp || item.timestamp)}
                      </div>
                    </div>
                    
                    <div className="feedback-rating-section">
                      {renderStars(item.rating)}
                      <span className="rating-text">
                        {item.rating === 5 && 'Excellent'}
                        {item.rating === 4 && 'Very Good'}
                        {item.rating === 3 && 'Good'}
                        {item.rating === 2 && 'Fair'}
                        {item.rating === 1 && 'Poor'}
                      </span>
                    </div>
                    
                    {item.comment && (
                      <div className="feedback-comment-box">
                        💬 "{item.comment}"
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FeedbackViewer;
