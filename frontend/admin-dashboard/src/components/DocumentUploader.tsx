import React, { useState, useRef } from 'react';
import api from '../services/api';
import { DocumentUploadResponse } from '../types/index';
import '../styles/DocumentUploader.css';

interface DocumentUploaderProps {
  onUploadSuccess?: (response: DocumentUploadResponse) => void;
  onUploadError?: (error: string) => void;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    try {
      setUploading(true);
      setProgress(0);

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', file.name);

        try {
          const response = await api.uploadDocument(formData);
          setProgress(((i + 1) / files.length) * 100);
          onUploadSuccess?.(response);
        } catch (error) {
          const errorMsg =
            error instanceof Error ? error.message : 'Failed to upload file';
          onUploadError?.(`Error uploading ${file.name}: ${errorMsg}`);
        }
      }
    } finally {
      setUploading(false);
      setProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div
      className={`document-uploader ${dragActive ? 'active' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleChange}
        accept=".pdf,.docx,.txt,.html,.md"
        disabled={uploading}
        style={{ display: 'none' }}
      />

      <div className="uploader-content">
        <div className="uploader-icon">📄</div>
        <h3>Drop documents here or click to browse</h3>
        <p>Supported formats: PDF, DOCX, TXT, HTML, MD</p>

        <button
          className="btn btn-primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Select Files'}
        </button>

        {uploading && (
          <div className="uploader-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <p>{Math.round(progress)}%</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUploader;
