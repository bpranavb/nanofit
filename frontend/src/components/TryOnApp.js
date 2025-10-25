import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import CameraCapture from './CameraCapture';
import HistoryPanel from './HistoryPanel';
import '../styles/TryOnApp.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TryOnApp = () => {
  const navigate = useNavigate();
  const [personImage, setPersonImage] = useState(null);
  const [clothingImage, setClothingImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [cameraType, setCameraType] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  const personInputRef = useRef(null);
  const clothingInputRef = useRef(null);

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('tryonHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save history to localStorage
  const saveToHistory = (personImg, clothingImg, resultImg) => {
    const newItem = {
      personImage: personImg,
      clothingImage: clothingImg,
      resultImage: resultImg,
      timestamp: new Date().toISOString()
    };
    const updatedHistory = [newItem, ...history];
    setHistory(updatedHistory);
    localStorage.setItem('tryonHistory', JSON.stringify(updatedHistory));
  };

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:image/...;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  // Handle camera capture
  const openCamera = (type) => {
    setCameraType(type);
    setShowCamera(true);
  };

  const handleCameraCapture = (base64, previewUrl) => {
    if (cameraType === 'person') {
      setPersonImage({ base64, preview: previewUrl });
    } else {
      setClothingImage({ base64, preview: previewUrl });
    }
    setError(null);
  };

  // Handle image upload
  const handleImageUpload = async (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const base64 = await fileToBase64(file);
      const previewUrl = URL.createObjectURL(file);
      
      if (type === 'person') {
        setPersonImage({ base64, preview: previewUrl });
      } else {
        setClothingImage({ base64, preview: previewUrl });
      }
      setError(null);
    } catch (err) {
      setError('Failed to process image. Please try again.');
      console.error('Error processing image:', err);
    }
  };

  // Handle paste
  const handlePaste = async (e, type) => {
    const items = e.clipboardData.items;
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        const base64 = await fileToBase64(file);
        const previewUrl = URL.createObjectURL(file);
        
        if (type === 'person') {
          setPersonImage({ base64, preview: previewUrl });
        } else {
          setClothingImage({ base64, preview: previewUrl });
        }
        setError(null);
        break;
      }
    }
  };

  // Handle drag and drop
  const handleDrop = async (e, type) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files[0];
    if (!file || !file.type.startsWith('image/')) {
      setError('Please drop a valid image file');
      return;
    }

    try {
      const base64 = await fileToBase64(file);
      const previewUrl = URL.createObjectURL(file);
      
      if (type === 'person') {
        setPersonImage({ base64, preview: previewUrl });
      } else {
        setClothingImage({ base64, preview: previewUrl });
      }
      setError(null);
    } catch (err) {
      setError('Failed to process image. Please try again.');
      console.error('Error processing image:', err);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  // Generate try-on
  const handleGenerate = async () => {
    if (!personImage || !clothingImage) {
      setError('Please upload both your photo and the clothing image');
      return;
    }

    setLoading(true);
    setError(null);
    setResultImage(null);
    setLoadingMessage('Preparing images...');

    try {
      console.log('Sending try-on request to:', `${API}/tryon`);
      
      setLoadingMessage('Creating your virtual try-on...');
      
      const response = await axios.post(`${API}/tryon`, {
        person_image: personImage.base64,
        clothing_image: clothingImage.base64
      });

      console.log('Try-on response received:', response.data);
      setLoadingMessage('Finalizing your new look...');

      if (response.data && response.data.result_image) {
        // The result_image is already base64, just add the data URL prefix for display
        const resultImageUrl = `data:image/png;base64,${response.data.result_image}`;
        setResultImage(resultImageUrl);
        setLoadingMessage('Complete!');
        
        // Save to history
        saveToHistory(personImage.preview, clothingImage.preview, resultImageUrl);
      } else {
        throw new Error('No image returned from server');
      }
    } catch (err) {
      console.error('Error generating try-on:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to generate try-on. Please try again.'
      );
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  // Start over function
  const handleStartOver = () => {
    setPersonImage(null);
    setClothingImage(null);
    setResultImage(null);
    setError(null);
    setLoadingMessage('');
  };

  // Clear history
  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      setHistory([]);
      localStorage.removeItem('tryonHistory');
    }
  };

  // Download result
  const handleDownload = () => {
    if (!resultImage) return;
    
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `virtual-tryon-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Share via email
  const handleEmailShare = () => {
    if (!resultImage) return;
    
    const subject = encodeURIComponent('Check out my Virtual Try-On!');
    const body = encodeURIComponent('I tried on clothes virtually! Check out the result.');
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  // Generate QR code for sharing
  const handleQRShare = () => {
    if (!resultImage) return;
    
    // For now, show a simple alert. In production, you'd use a QR code library
    alert('QR Code sharing: This would generate a QR code linking to your result. (Feature coming soon!)');
  };

  // Load from history
  const handleHistorySelect = (item) => {
    // Convert data URLs back to the format we need
    setPersonImage({ 
      base64: item.personImage.split(',')[1], 
      preview: item.personImage 
    });
    setClothingImage({ 
      base64: item.clothingImage.split(',')[1], 
      preview: item.clothingImage 
    });
    setResultImage(item.resultImage);
  };

  return (
    <div className="tryon-app">
      {/* Camera Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
          type={cameraType}
        />
      )}

      {/* History Panel */}
      {showHistory && (
        <HistoryPanel
          history={history}
          onClose={() => setShowHistory(false)}
          onSelect={handleHistorySelect}
        />
      )}

      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Back
          </button>
          <h1 className="app-title">Virtual Try-On</h1>
          <div className="header-actions">
            <button className="header-button" onClick={() => setShowHistory(true)}>
              📋 History ({history.length})
            </button>
            {history.length > 0 && (
              <button className="header-button clear" onClick={handleClearHistory}>
                🗑️ Clear
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="app-container">
        {/* Input Section */}
        <div className="input-section">
          {/* Person Image Upload */}
          <div className="upload-card">
            <h3 className="upload-title">Your Photo</h3>
            <div 
              className="upload-area"
              onClick={() => personInputRef.current?.click()}
              onDrop={(e) => handleDrop(e, 'person')}
              onDragOver={handleDragOver}
              onPaste={(e) => handlePaste(e, 'person')}
              tabIndex={0}
            >
              {personImage ? (
                <img 
                  src={personImage.preview} 
                  alt="Your photo" 
                  className="preview-image"
                />
              ) : (
                <div className="upload-placeholder">
                  <span className="upload-icon">📸</span>
                  <p className="upload-text">Tap to upload your photo</p>
                  <p className="upload-hint">or drag and drop</p>
                </div>
              )}
            </div>
            <input
              ref={personInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => handleImageUpload(e, 'person')}
              style={{ display: 'none' }}
            />
            <div className="upload-actions">
              <button 
                className="upload-action-button camera"
                onClick={(e) => { e.stopPropagation(); openCamera('person'); }}
              >
                📷 Take Photo
              </button>
              <button 
                className="upload-action-button gallery"
                onClick={() => personInputRef.current?.click()}
              >
                🖼️ From Gallery
              </button>
            </div>
          </div>

          {/* Clothing Image Upload */}
          <div className="upload-card">
            <h3 className="upload-title">Clothing Photo</h3>
            <div 
              className="upload-area"
              onClick={() => clothingInputRef.current?.click()}
              onDrop={(e) => handleDrop(e, 'clothing')}
              onDragOver={handleDragOver}
              onPaste={(e) => handlePaste(e, 'clothing')}
              tabIndex={0}
            >
              {clothingImage ? (
                <img 
                  src={clothingImage.preview} 
                  alt="Clothing" 
                  className="preview-image"
                />
              ) : (
                <div className="upload-placeholder">
                  <span className="upload-icon">👗</span>
                  <p className="upload-text">Tap to upload clothing</p>
                  <p className="upload-hint">or drag and drop</p>
                </div>
              )}
            </div>
            <input
              ref={clothingInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => handleImageUpload(e, 'clothing')}
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {/* Action Section */}
        <div className="action-section">
          <button 
            className="generate-button"
            onClick={handleGenerate}
            disabled={loading || !personImage || !clothingImage}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              'Generate Try-On'
            )}
          </button>
          
          {loading && loadingMessage && (
            <p className="loading-message">{loadingMessage}</p>
          )}
          
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
        </div>

        {/* Result Section */}
        {resultImage && (
          <div className="result-section">
            <h3 className="result-title">Your Virtual Try-On Result</h3>
            <div className="result-container">
              <img 
                src={resultImage} 
                alt="Try-on result" 
                className="result-image"
              />
            </div>
            <div className="action-section" style={{ marginTop: '2rem' }}>
              <button 
                className="generate-button"
                onClick={handleStartOver}
                style={{ background: 'linear-gradient(135deg, #b19cd9 0%, #dda0dd 100%)' }}
              >
                Start Over
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TryOnApp;
