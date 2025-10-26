import React, { useState } from 'react';
import axios from 'axios';
import '../styles/FeedbackForm.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FeedbackForm = ({ tryonId, onClose }) => {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [comment, setComment] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (rating === 0) {
      setError('Please select a rating');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await axios.post(`${API}/feedback`, {
        tryon_id: tryonId,
        rating: rating,
        comment: comment || null,
        customer_name: customerName || null
      });

      setSubmitted(true);
      
      // Auto-close after 2 seconds
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err) {
      console.error('Error submitting feedback:', err);
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="feedback-form">
        <div className="feedback-success">
          <div className="success-icon">✓</div>
          <h3>Thank You!</h3>
          <p>Your feedback has been recorded.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-form">
      <div className="feedback-header">
        <h3>How was your experience?</h3>
        <button className="feedback-close" onClick={onClose}>×</button>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Star Rating */}
        <div className="rating-section">
          <label>Rating</label>
          <div className="stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className={`star ${
                  star <= (hoveredRating || rating) ? 'active' : ''
                }`}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredRating(star)}
                onMouseLeave={() => setHoveredRating(0)}
              >
                ★
              </button>
            ))}
          </div>
          {rating > 0 && (
            <span className="rating-text">
              {rating === 1 && 'Poor'}
              {rating === 2 && 'Fair'}
              {rating === 3 && 'Good'}
              {rating === 4 && 'Very Good'}
              {rating === 5 && 'Excellent'}
            </span>
          )}
        </div>

        {/* Customer Name (Optional) */}
        <div className="form-field">
          <label>Your Name (Optional)</label>
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="Enter your name"
            className="text-input"
          />
        </div>

        {/* Comment (Optional) */}
        <div className="form-field">
          <label>Comments (Optional)</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your thoughts about the virtual try-on..."
            rows={4}
            className="text-input"
          />
        </div>

        {error && (
          <div className="feedback-error">{error}</div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="submit-feedback-button"
          disabled={submitting || rating === 0}
        >
          {submitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  );
};

export default FeedbackForm;
