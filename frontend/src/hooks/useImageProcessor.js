import { useState, useCallback } from 'react';

const useImageProcessor = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processError, setProcessError] = useState(null);

  // Modern Image Resizer using createImageBitmap (better for Mobile/HEIC)
  const resizeImage = async (file, maxWidth = 1024, maxHeight = 1024) => {
    try {
      // Attempt 1: createImageBitmap (Fastest & Modern)
      // We prioritize this for Android/Tablets
      let bitmap = null;
      try {
        bitmap = await createImageBitmap(file);
      } catch (bitmapError) {
        console.warn('createImageBitmap failed, falling back to FileReader:', bitmapError);
      }

      if (bitmap) {
        let width = bitmap.width;
        let height = bitmap.height;

        if (width > height) {
          if (width > maxWidth) {
            height = Math.round((height * maxWidth) / width);
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = Math.round((width * maxHeight) / height);
            height = maxHeight;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(bitmap, 0, 0, width, height);
        
        // High quality output
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        const base64 = dataUrl.split(',')[1];
        bitmap.close(); 
        return { base64, preview: dataUrl };
      }

      // Attempt 2: FileReader + Image (Legacy/Fallback)
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            let width = img.width;
            let height = img.height;

            if (width > height) {
              if (width > maxWidth) {
                height = Math.round((height * maxWidth) / width);
                width = maxWidth;
              }
            } else {
              if (height > maxHeight) {
                width = Math.round((width * maxHeight) / height);
                height = maxHeight;
              }
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
            const base64 = dataUrl.split(',')[1];
            resolve({ base64, preview: dataUrl });
          };
          
          img.onerror = (err) => {
            reject(new Error('Image format unsupported by browser. Please try a screenshot or different photo.'));
          };
          
          img.src = event.target.result;
        };
        reader.onerror = (err) => reject(err);
      });

    } catch (err) {
      throw err;
    }
  };

  const processFile = useCallback(async (file) => {
    setIsProcessing(true);
    setProcessError(null);
    try {
      const result = await resizeImage(file);
      setIsProcessing(false);
      return result;
    } catch (err) {
      setIsProcessing(false);
      setProcessError(err.message || 'Failed to process image');
      throw err;
    }
  }, []);

  return { processFile, isProcessing, processError };
};

export default useImageProcessor;
