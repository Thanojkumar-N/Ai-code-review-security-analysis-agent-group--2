import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { 
  Settings as SettingsIcon, 
  FolderPlus, 
  Database, 
  ShieldCheck, 
  AlertTriangle,
  Server
} from 'lucide-react';

interface SystemHealth {
  status: string;
  environment: string;
  database: string;
}

export const Settings: React.FC = () => {
  const { createProject } = useAuth();
  
  // Project Container States
  const [projName, setProjName] = useState('');
  const [projDesc, setProjDesc] = useState('');
  const [projLoading, setProjLoading] = useState(false);
  const [projSuccess, setProjSuccess] = useState(false);
  const [projError, setProjError] = useState<string | null>(null);

  // System Health States
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  useEffect(() => {
    const fetchHealth = async () => {
      setHealthLoading(true);
      try {
        const response = await apiClient.get<SystemHealth>('/system/health');
        setHealth(response.data);
      } catch (err) {
        console.error('Failed to contact health check endpoint', err);
      } finally {
        setHealthLoading(false);
      }
    };

    fetchHealth();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projName.trim()) return;
    
    setProjLoading(true);
    setProjSuccess(false);
    setProjError(null);

    try {
      await createProject(projName, projDesc);
      setProjSuccess(true);
      setProjName('');
      setProjDesc('');
    } catch (err: any) {
      setProjError(err.response?.data?.detail || 'Failed to create workspace project.');
    } finally {
      setProjLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
          System Settings
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Manage workspace project definitions and monitor backend connection nodes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        
        {/* Create Project Workspace */}
        <div className="md:col-span-7 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderPlus className="h-5 w-5 text-primary" />
                <span>New Project Container</span>
              </CardTitle>
              <CardDescription>
                Create a dedicated compartment to isolate and review unique repositories.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateProject} className="space-y-4">
                {projSuccess && (
                  <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
                    <ShieldCheck className="h-4 w-4 flex-shrink-0" />
                    <span>Project workspace container created successfully!</span>
                  </div>
                )}
                {projError && (
                  <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    <span>{projError}</span>
                  </div>
                )}
                <Input
                  label="Project Title"
                  placeholder="e.g. Fintech API service"
                  value={projName}
                  onChange={(e) => setProjName(e.target.value)}
                  required
                />
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Description (Optional)
                  </label>
                  <textarea
                    placeholder="Enter project summary details..."
                    value={projDesc}
                    onChange={(e) => setProjDesc(e.target.value)}
                    className="flex min-h-[80px] w-full rounded-lg border border-input bg-background/50 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200"
                  />
                </div>
                <Button type="submit" isLoading={projLoading} className="w-full">
                  Create Container
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* System Diagnostics status */}
        <div className="md:col-span-5 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                <span>Backend Diagnostics</span>
              </CardTitle>
              <CardDescription>
                System environment variables and relational database links status.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              {healthLoading ? (
                <div className="flex h-20 items-center justify-center">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
                </div>
              ) : health ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-border/40 pb-2">
                    <span className="text-muted-foreground text-xs">System Node Status</span>
                    <span className="inline-flex items-center gap-1.5 font-semibold text-green-500 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded-full text-[10px]">
                      <Server className="h-3 w-3" />
                      <span>{health.status}</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-border/40 pb-2">
                    <span className="text-muted-foreground text-xs">Relational Database Link</span>
                    <span className="inline-flex items-center gap-1.5 font-semibold text-green-500 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded-full text-[10px]">
                      <Database className="h-3 w-3" />
                      <span>{health.database}</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground text-xs">Environment Node</span>
                    <span className="font-mono text-xs font-bold text-foreground">
                      {health.environment}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-destructive bg-destructive/10 p-3 border border-destructive/20 rounded-lg text-xs">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Failed to ping health diagnostics. Check FastAPI daemon logs.</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
};
export default Settings;
