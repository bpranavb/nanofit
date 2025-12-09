import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import CameraCapture from './CameraCapture';
import HistoryPanel from './HistoryPanel';
import FeedbackForm from './FeedbackForm';
import FeedbackViewer from './FeedbackViewer';
import '../styles/TryOnApp.css';
import LoadingOverlay from './LoadingOverlay';
import UploadCard from './UploadCard';
import useImageProcessor from '../hooks/useImageProcessor';

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
  const [showFeedback, setShowFeedback] = useState(false);
  const { processFile } = useImageProcessor();
  const [showFeedbackViewer, setShowFeedbackViewer] = useState(false);
  const [currentTryonId, setCurrentTryonId] = useState(null);
  
  const personInputRef = useRef(null);
  const clothingInputRef = useRef(null);

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('tryonHistory');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        // Keep only last 20 items on load
        const limited = parsed.slice(0, 20);
        setHistory(limited);
        if (limited.length < parsed.length) {
          localStorage.setItem('tryonHistory', JSON.stringify(limited));
        }
      } catch (e) {
        console.error('Error loading history:', e);
        localStorage.removeItem('tryonHistory');
        setHistory([]);
      }
    }
  }, []);
  // Enhanced Thinking UI
  useEffect(() => {
    if (!loading) return;

    const steps = [
      "Analyzing body pose...",
      "Identifying clothing structure...",
      "Mapping fabric physics...",
      "Generating photorealistic texture...",
      "Finalizing lighting and shadows...",
      "Applying finishing touches..."
    ];
    
    let stepIndex = 0;
    setLoadingMessage(steps[0]);

    const intervalId = setInterval(() => {
      stepIndex = (stepIndex + 1) % steps.length;
      setLoadingMessage(steps[stepIndex]);
    }, 2500); // Change message every 2.5 seconds

    return () => clearInterval(intervalId);
  }, [loading]);


  // Save history to localStorage with size limit
  const saveToHistory = (personImg, clothingImg, resultImg) => {
    const newItem = {
      personImage: personImg,
      clothingImage: clothingImg,
      resultImage: resultImg,
      timestamp: new Date().toISOString()
    };
    
    // Keep only last 20 items to prevent localStorage overflow
    const updatedHistory = [newItem, ...history].slice(0, 20);
    
    try {
      setHistory(updatedHistory);
      localStorage.setItem('tryonHistory', JSON.stringify(updatedHistory));
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        console.log('Storage quota exceeded, clearing old history...');
        // Keep only last 10 items if we hit quota
        const reducedHistory = [newItem, ...history].slice(0, 10);
        setHistory(reducedHistory);
        try {
          localStorage.setItem('tryonHistory', JSON.stringify(reducedHistory));
        } catch (err) {
          // If still failing, just keep current session
          console.error('Unable to save history:', err);
          setHistory([newItem]);
          localStorage.setItem('tryonHistory', JSON.stringify([newItem]));
        }
      } else {
        console.error('Error saving history:', e);
      }
    }
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
  // Resize image before converting to base64
  // Helper: Get file extension/type
  const getFileType = (file) => {
    return file.type || 'unknown';
  };

  // Image processing logic moved to useImageProcessor hook

  // (Duplicate function removed)


  // Handle camera capture
  const openCamera = (type) => {
    setCameraType(type);
    setShowCamera(true);
  };

  const handleCameraCapture = async (base64, previewUrl) => {
    // Camera images might be large too, but base64 is already passed.
    // For consistency, we could rely on camera capture settings (already set to 720p/1080p).
    // But let's verify if we need to resize. 
    // Actually, CameraCapture component already gives us a data URL.
    // Let's create a file object from it to reuse resizeImage, or just assume Camera is okay.
    // Given the prompt "Implemented Smart Compression", let's be safe and compress this too if needed.
    // But wait, `resizeImage` takes a file. Let's make a variant or just use as is for now 
    // since CameraCapture sets specific resolution. 
    // Actually, better to just use what we have, as CameraCapture explicitly sets width/height.
    
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

    // Debug Alert 1
    // alert(`Selected: ${file.name} (${(file.size/1024/1024).toFixed(2)}MB)`);

    setLoading(true);
    setLoadingMessage('Processing image...');
    setError(null);

    try {
      console.log(`Uploading ${type}:`, file.name, file.type, file.size);
      
      // Compress and resize using modern method
      const { base64, preview } = await processFile(file);
      
      // Debug Alert 2
      // alert('Resize successful');

      if (type === 'person') {
        setPersonImage({ base64, preview });
      } else {
        setClothingImage({ base64, preview });
      }
    } catch (err) {
      // Handle specific errors
      let errorMsg = 'Failed to process image. Please try a different photo.';
      if (err.message && err.message.includes('Format')) {
         errorMsg = err.message;
      }
      setError(errorMsg);
      console.error('Error processing image:', err);
      alert(`Error: ${errorMsg}\nDetails: ${err.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  // Handle paste
  const handlePaste = async (e, type) => {
    const items = e.clipboardData.items;
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        try {
          const { base64, preview } = await processFile(file);
          
          if (type === 'person') {
            setPersonImage({ base64, preview });
          } else {
            setClothingImage({ base64, preview });
          }
          setError(null);
        } catch (err) {
          console.error('Error processing pasted image:', err);
          setError('Failed to process pasted image');
        }
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
      // Compress and resize using modern method
      const { base64, preview } = await processFile(file);
      
      if (type === 'person') {
        setPersonImage({ base64, preview });
      } else {
        setClothingImage({ base64, preview });
      }
      setError(null);
    } catch (err) {
      // Handle specific errors
      if (err.message && err.message.includes('Format might be unsupported')) {
         setError('Image format not supported (likely HEIC). Please use JPEG or PNG, or take a photo directly.');
      } else {
         setError('Failed to process image. Please try a different photo.');
      }
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
      
      // Loading message handled by effect now
      
      const response = await axios.post(`${API}/tryon`, {
        person_image: personImage.base64,
        clothing_image: clothingImage.base64
      });

      console.log('Try-on response received:', response.data);
      // Final message set by effect or success state logic below

      if (response.data && response.data.result_image) {
        // The result_image is already base64, just add the data URL prefix for display
        const resultImageUrl = `data:image/png;base64,${response.data.result_image}`;
        setResultImage(resultImageUrl);
        setLoadingMessage('Complete!');
        setCurrentTryonId(response.data.id);
        
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

      {/* Feedback Viewer */}
      {showFeedbackViewer && (
        <FeedbackViewer
          onClose={() => setShowFeedbackViewer(false)}
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
            <button className="header-button" onClick={() => setShowFeedbackViewer(true)}>
              ⭐ Feedback
            </button>
            <button className="header-button" onClick={() => setShowHistory(true)}>
              📋 History ({history.length}/20)
            </button>
            {history.length > 15 && (
              <span className="storage-warning">⚠️ Near limit</span>
            )}
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
            <label 
              className="upload-area"
              htmlFor="person-upload"
              onDrop={(e) => handleDrop(e, 'person')}
              onDragOver={handleDragOver}
              onPaste={(e) => handlePaste(e, 'person')}
              tabIndex={0}
              style={{ display: 'flex', cursor: 'pointer' }}
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
            </label>
            <input
              id="person-upload"
              ref={personInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => {
                console.log('Person Input Changed', e.target.files);
                handleImageUpload(e, 'person');
              }}
              onClick={(e) => e.target.value = null}
              style={{ position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap', border: 0 }}
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
                onClick={() => document.getElementById('person-upload').click()}
              >
                🖼️ From Gallery
              </button>
            </div>
          </div>

          {/* Clothing Image Upload */}
          <div className="upload-card">
            <h3 className="upload-title">Clothing Photo</h3>
            <label 
              className="upload-area"
              htmlFor="clothing-upload"
              onDrop={(e) => handleDrop(e, 'clothing')}
              onDragOver={handleDragOver}
              onPaste={(e) => handlePaste(e, 'clothing')}
              tabIndex={0}
              style={{ display: 'flex', cursor: 'pointer' }}
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
            </label>
            <input
              id="clothing-upload"
              ref={clothingInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => {
                console.log('Clothing Input Changed', e.target.files);
                handleImageUpload(e, 'clothing');
              }}
              onClick={(e) => e.target.value = null}
              style={{ position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap', border: 0 }}
            />
            <div className="upload-actions">
              <button 
                className="upload-action-button camera"
                onClick={(e) => { e.stopPropagation(); openCamera('clothing'); }}
              >
                📷 Take Photo
              </button>
              <button 
                className="upload-action-button gallery"
                onClick={() => document.getElementById('clothing-upload').click()}
              >
                🖼️ From Gallery
              </button>
            </div>
          </div>
        </div>

        {/* Action Section */}
        <div className="action-section">
          <button 
            className="generate-button"
            onClick={handleGenerate}
            disabled={loading || !personImage || !clothingImage}
          >
            {loading ? 'Generating...' : 'Generate Try-On'}
          </button>
          
          {/* loadingMessage removed - moved to overlay */}
          
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
            
            {/* Share Options */}
            <div className="share-section">
              <h4 className="share-title">Share Your Result</h4>
              <div className="share-buttons">
                <button className="share-button download" onClick={handleDownload}>
                  ⬇️ Download
                </button>
                <button className="share-button email" onClick={handleEmailShare}>
                  ✉️ Email
                </button>
                <button className="share-button qr" onClick={handleQRShare}>
                  📱 QR Code
                </button>
              </div>
            </div>

            {/* Feedback Section */}
            {!showFeedback ? (
              <div className="feedback-prompt">
                <button 
                  className="feedback-button"
                  onClick={() => setShowFeedback(true)}
                >
                  💬 Share Your Feedback
                </button>
              </div>
            ) : (
              <FeedbackForm 
                tryonId={currentTryonId}
                onClose={() => setShowFeedback(false)}
              />
            )}

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
      {/* Loading Overlay */}
      {loading && <LoadingOverlay message={loadingMessage} />}
    </div>
  );
};

export default TryOnApp;
