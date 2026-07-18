import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import { Upload, AlertTriangle, FileCode, CheckCircle2 } from 'lucide-react';

const MAX_SIZE_BYTES = 5242880; // 5MB

export const UploadCode: React.FC = () => {
  const { activeProject, projects, selectProject } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  
  const navigate = useNavigate();

  const validateFile = (selectedFile: File): boolean => {
    setError(null);

    // 1. Validate Extension
    const fileExt = selectedFile.name.split('.').pop()?.toLowerCase();
    if (fileExt !== 'py' && fileExt !== 'java') {
      setError('Invalid file format. Only Python (.py) and Java (.java) source files are allowed.');
      setFile(null);
      return false;
    }

    // 2. Validate Size
    if (selectedFile.size > MAX_SIZE_BYTES) {
      setError('File size exceeds the 5MB maximum limit. Please submit a smaller file.');
      setFile(null);
      return false;
    }

    setFile(selectedFile);
    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateFile(e.target.files[0]);
    }
  };

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const proj = projects.find((p) => p.id === e.target.value);
    if (proj) selectProject(proj);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or drop a valid file first.');
      return;
    }
    if (!activeProject) {
      setError('Select a workspace project container first.');
      return;
    }

    setError(null);
    setLoading(true);
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', activeProject.id);

    try {
      const response = await apiClient.post('/submissions/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(true);
      
      // Navigate to results screen after brief timeout
      setTimeout(() => {
        const reportId = response.data.id;
        navigate(`/results?report=${reportId}`);
      }, 1000);

    } catch (err: any) {
      // Catch detailed syntax parsing or extension errors returned by backend service
      setError(
        err.response?.data?.detail || 'Failed to submit file upload. Confirm formatting structure.'
      );
    } finally {
      setLoading(false);
    }
  };

  const projectOptions = projects.map((p) => ({
    value: p.id,
    label: p.name,
  }));

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
          Upload Code File
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload Python (.py) or Java (.java) source scripts for syntax validation and SAST auditing.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Submit Script Container</CardTitle>
          <CardDescription>
            Choose a target project workspace, drag script in file container, and execute review.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Project selection target */}
            {projects.length > 0 && (
              <Select
                label="Target Workspace Project"
                options={projectOptions}
                value={activeProject?.id || ''}
                onChange={handleProjectSelect}
              />
            )}

            {/* Error notifications */}
            {error && (
              <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span className="font-mono">{error}</span>
              </div>
            )}

            {/* Success notifications */}
            {success && (
              <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <span>Upload completed successfully! Loading analysis reviews workspace...</span>
              </div>
            )}

            {/* Drag and drop panel */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                dragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border/60 hover:border-primary/50 bg-background/30'
              }`}
            >
              <input
                id="file-upload-input"
                type="file"
                className="hidden"
                accept=".py,.java"
                onChange={handleFileChange}
              />
              
              <label htmlFor="file-upload-input" className="cursor-pointer w-full h-full">
                <div className="flex flex-col items-center justify-center space-y-3">
                  <div className="rounded-xl bg-primary/10 p-3 border border-primary/20 text-primary">
                    <Upload className="h-6 w-6" />
                  </div>
                  
                  {file ? (
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-foreground flex items-center justify-center gap-1.5">
                        <FileCode className="h-4 w-4 text-primary" />
                        <span>{file.name}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-foreground">
                        Drag and drop your file here, or <span className="text-primary hover:underline">browse files</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Only Python (.py) and Java (.java) source scripts are supported (Max 5MB)
                      </p>
                    </div>
                  )}
                </div>
              </label>
            </div>

            {/* Submit details trigger */}
            <Button
              type="submit"
              isLoading={loading}
              className="w-full flex items-center justify-center gap-2"
              disabled={!file}
            >
              <Upload className="h-4 w-4" />
              <span>Audit Uploaded Code</span>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
export default UploadCode;
