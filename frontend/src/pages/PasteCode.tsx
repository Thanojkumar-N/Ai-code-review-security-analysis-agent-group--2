import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Editor from '@monaco-editor/react';
import { FileCode, AlertTriangle, CheckCircle2 } from 'lucide-react';

const PYTHON_TEMPLATE = `def greet(name: str) -> None:
    print(f"Hello, {name}!")

if __name__ == "__main__":
    greet("Developer")
`;

const JAVA_TEMPLATE = `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Developer!");
    }
}
`;

export const PasteCode: React.FC = () => {
  const { activeProject, projects, selectProject } = useAuth();
  
  // States
  const [language, setLanguage] = useState<'python' | 'java'>('python');
  const [code, setCode] = useState(PYTHON_TEMPLATE);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedLang = e.target.value as 'python' | 'java';
    setLanguage(selectedLang);
    // Auto populate template
    setCode(selectedLang === 'python' ? PYTHON_TEMPLATE : JAVA_TEMPLATE);
  };

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const proj = projects.find((p) => p.id === e.target.value);
    if (proj) selectProject(proj);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('Please paste or write some code before submitting.');
      return;
    }
    if (!activeProject) {
      setError('Select a workspace project container first.');
      return;
    }

    setError(null);
    setLoading(true);
    setSuccess(false);

    try {
      const response = await apiClient.post('/submissions/paste-code', {
        project_id: activeProject.id,
        submission_type: 'paste',
        raw_code: code,
        language: language,
      });

      setSuccess(true);
      
      // Navigate to results page after short delay
      setTimeout(() => {
        const reportId = response.data.id;
        navigate(`/results?report=${reportId}`);
      }, 1000);

    } catch (err: any) {
      // Capture detailed syntax error reports returned by Python AST or Java brace validation
      setError(
        err.response?.data?.detail || 'Failed to submit code contents. Verify API connectivity.'
      );
    } finally {
      setLoading(false);
    }
  };

  const projectOptions = projects.map((p) => ({
    value: p.id,
    label: p.name,
  }));

  const languageOptions = [
    { value: 'python', label: 'Python (.py)' },
    { value: 'java', label: 'Java (.java)' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
          Submit Source Code Snippet
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Paste or write code in Monaco Editor and run syntax checking and SAST auditing.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Interactive Code Editor Workspace</CardTitle>
          <CardDescription>
            Select project, choose language mode, write scripts, and execute analysis checks.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Grid for Target Project and Language selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.length > 0 && (
                <Select
                  label="Target Workspace Project"
                  options={projectOptions}
                  value={activeProject?.id || ''}
                  onChange={handleProjectSelect}
                />
              )}

              <Select
                label="Source Syntax Language"
                options={languageOptions}
                value={language}
                onChange={handleLanguageChange}
              />
            </div>

            {/* Error notifications (especially Syntax Validation reports) */}
            {error && (
              <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <div className="font-mono whitespace-pre-wrap">{error}</div>
              </div>
            )}

            {/* Success notifications */}
            {success && (
              <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <span>Code compiled and passed syntax check! Starting audit analysis...</span>
              </div>
            )}

            {/* Monaco Editor Container */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Monaco Editor Panel ({language === 'python' ? 'Python Mode' : 'Java Mode'})
              </label>
              <div className="rounded-lg border border-border bg-[#1e1e1e] overflow-hidden focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 focus-within:ring-offset-background">
                {/* Editor Mimic Header */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-border/60 bg-muted/20">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-red-500/30"></span>
                      <span className="w-3 h-3 rounded-full bg-yellow-500/30"></span>
                      <span className="w-3 h-3 rounded-full bg-green-500/30"></span>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">
                      {language === 'python' ? 'main.py' : 'Main.java'}
                    </span>
                  </div>
                </div>

                {/* Monaco Editor */}
                <Editor
                  height="360px"
                  language={language}
                  value={code}
                  theme="vs-dark"
                  onChange={(val) => setCode(val || '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: 'JetBrains Mono, Fira Code, monospace',
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                  }}
                />
              </div>
            </div>

            {/* Submit details trigger */}
            <Button
              type="submit"
              isLoading={loading}
              className="w-full flex items-center justify-center gap-2"
              disabled={!code.trim()}
            >
              <FileCode className="h-4 w-4" />
              <span>Validate & Analyze Code</span>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
export default PasteCode;
