import React from 'react';
import { useNavigate } from 'react-router-dom';
import BeforeAfterSlider from './BeforeAfterSlider';
import '../styles/LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: "AI-Powered Try-On",
      description: "Experience the magic of trying on clothes virtually with advanced AI technology",
      icon: "✨"
    },
    {
      title: "Instant Results",
      description: "Get realistic try-on results in seconds, no waiting required",
      icon: "⚡"
    },
    {
      title: "High Quality",
      description: "Generate photorealistic images that look natural and professionally styled",
      icon: "🎨"
    }
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Virtual Try-On
            <span className="gradient-text"> Made Simple</span>
          </h1>
          <p className="hero-subtitle">
            See yourself in any outfit instantly with AI-powered virtual try-on technology.
            Upload your photo and the clothes you want to try - we'll do the rest!
          </p>
          <button 
            className="cta-button"
            onClick={() => navigate('/app')}
          >
            Start Trying On
            <span className="arrow">→</span>
          </button>
        </div>
        
        <div className="hero-image">
          <div className="demo-slider-container">
            <BeforeAfterSlider
              beforeImage="https://customer-assets.emergentagent.com/job_tablet-bugfix/artifacts/brlblti7_Gemini_Generated_Image_oh7qwjoh7qwjoh7q.png"
              afterImage="https://customer-assets.emergentagent.com/job_tablet-bugfix/artifacts/z4o9uu7w_Gemini_Generated_Image_oh7qwjoh7qwjoh7q%20%281%29.png"
              alt="Virtual Try-On Demo"
            />
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section">
        <h2 className="section-title">Why Choose Virtual Try-On?</h2>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How It Works Section */}
      <div className="how-it-works-section">
        <h2 className="section-title">How It Works</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <h3 className="step-title">Upload Your Photo</h3>
            <p className="step-description">Choose a clear photo of yourself</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">2</div>
            <h3 className="step-title">Select Clothing</h3>
            <p className="step-description">Upload a photo of the outfit</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">3</div>
            <h3 className="step-title">Get Results</h3>
            <p className="step-description">See yourself in the new outfit!</p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="cta-section">
        <h2 className="cta-title">Ready to Transform Your Style?</h2>
        <p className="cta-description">
          Start your virtual try-on experience now and see how you look in any outfit!
        </p>
        <button 
          className="cta-button secondary"
          onClick={() => navigate('/app')}
        >
          Get Started Free
        </button>
      </div>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 Virtual Try-On. Powered by AI.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
