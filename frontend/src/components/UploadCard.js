import React from 'react';

const UploadCard = ({
  title,
  id,
  image,
  placeholderIcon,
  placeholderText,
  onFileChange,
  onDrop,
  onPaste,
  onCamera,
  inputRef
}) => {
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div className="upload-card">
      <h3 className="upload-title">{title}</h3>
      <label 
        className="upload-area"
        htmlFor={id}
        onDrop={onDrop}
        onDragOver={handleDragOver}
        onPaste={onPaste}
        tabIndex={0}
        style={{ display: 'flex', cursor: 'pointer' }}
      >
        {image ? (
          <img 
            src={image.preview} 
            alt={title} 
            className="preview-image"
          />
        ) : (
          <div className="upload-placeholder">
            <span className="upload-icon">{placeholderIcon}</span>
            <p className="upload-text">{placeholderText}</p>
            <p className="upload-hint">or drag and drop</p>
          </div>
        )}
      </label>
      <input
        id={id}
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={onFileChange}
        onClick={(e) => e.target.value = null}
        style={{ 
          position: 'absolute', 
          width: 1, 
          height: 1, 
          padding: 0, 
          margin: -1, 
          overflow: 'hidden', 
          clip: 'rect(0,0,0,0)', 
          whiteSpace: 'nowrap', 
          border: 0 
        }}
      />
      <div className="upload-actions">
        <button 
          className="upload-action-button camera"
          onClick={(e) => { e.stopPropagation(); onCamera(); }}
        >
          📷 Take Photo
        </button>
        <button 
          className="upload-action-button gallery"
          onClick={() => document.getElementById(id).click()}
        >
          🖼️ From Gallery
        </button>
      </div>
    </div>
  );
};

export default UploadCard;
