import React, { useRef, useState, useEffect } from 'react';
import '../styles/CameraCapture.css';

const CameraCapture = ({ onCapture, onClose, type }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState(null);
  const [facingMode, setFacingMode] = useState('environment'); // Default to back camera

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [facingMode]); // Restart camera when facingMode changes

  const startCamera = async () => {
    // Stop any existing stream first
    stopCamera();
    
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 } 
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
      setError(null);
    } catch (err) {
      console.error('Error accessing camera:', err);
      // Fallback: If 'environment' fails, try any camera (e.g. laptop webcam)
      if (facingMode === 'environment') {
         console.log('Environment camera failed, trying default user camera');
         try {
            const fallbackStream = await navigator.mediaDevices.getUserMedia({
                video: true
            });
            if (videoRef.current) {
                videoRef.current.srcObject = fallbackStream;
            }
            setStream(fallbackStream);
            setError(null);
         } catch (fallbackErr) {
             setError('Unable to access camera. Please check permissions.');
         }
      } else {
         setError('Unable to access camera. Please check permissions.');
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (videoRef.current) {
        videoRef.current.srcObject = null;
    }
  };

  const toggleCamera = () => {
    setFacingMode(prevMode => prevMode === 'user' ? 'environment' : 'user');
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setCapturedImage(imageDataUrl);
  };

  const retakePhoto = () => {
    setCapturedImage(null);
  };

  const usePhoto = () => {
    if (capturedImage) {
      // Extract base64 from data URL
      const base64 = capturedImage.split(',')[1];
      onCapture(base64, capturedImage);
      stopCamera();
      onClose();
    }
  };

  return (
    <div className="camera-modal">
      <div className="camera-container">
        <div className="camera-header">
          <h2>Capture {type === 'person' ? 'Person' : 'Clothing'} Photo</h2>
          <button className="camera-button switch" onClick={toggleCamera}>
            <span className="camera-icon">🔄</span>
            Switch
          </button>
          <button className="close-button" onClick={() => { stopCamera(); onClose(); }}>
            ✕
          </button>
        </div>

        <div className="camera-content">
          {error ? (
            <div className="camera-error">
              <p>{error}</p>
              <button className="retry-button" onClick={startCamera}>Retry</button>
            </div>
          ) : (
            <>
              {!capturedImage ? (
                <>
                  <video ref={videoRef} autoPlay playsInline className="camera-video" />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                </>
              ) : (
                <img src={capturedImage} alt="Captured" className="captured-preview" />
              )}
            </>
          )}
        </div>

        <div className="camera-controls">
          {!capturedImage ? (
            <>
              <button className="camera-button capture" onClick={capturePhoto}>
                <span className="camera-icon">📷</span>
                Capture
              </button>
            </>
          ) : (
            <>
              <button className="camera-button retake" onClick={retakePhoto}>
                ↻ Retake
              </button>
              <button className="camera-button use" onClick={usePhoto}>
                ✓ Use Photo
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraCapture;
