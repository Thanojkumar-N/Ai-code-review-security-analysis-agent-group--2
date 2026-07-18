import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import { 
  Folder, 
  Calendar, 
  Terminal, 
  Activity, 
  Filter, 
  ArrowRight, 
  ChevronLeft, 
  ChevronRight,
  FileCode,
  Layers,
  FileSpreadsheet
} from 'lucide-react';

interface ProjectDetail {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface SubmissionItem {
  id: string;
  project_id: string;
  submission_type: string;
  file_path?: string;
  raw_code?: string;
  status: string;
  created_at: string;
}

interface PaginatedSubmissions {
  items: SubmissionItem[];
  total: int;
  page: int;
  size: int;
  pages: int;
}

export const ProjectDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  // States
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [submissionsData, setSubmissionsData] = useState<PaginatedSubmissions | null>(null);
  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingSubmissions, setLoadingSubmissions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const size = 5; // Display 5 submission records per subpage

  const fetchProjectDetails = async () => {
    if (!id) return;
    setLoadingProject(true);
    try {
      const response = await apiClient.get<ProjectDetail>(`/projects/${id}`);
      setProject(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project details.');
    } finally {
      setLoadingProject(false);
    }
  };

  const fetchSubmissions = async () => {
    if (!id) return;
    setLoadingSubmissions(true);
    try {
      const response = await apiClient.get<PaginatedSubmissions>(`/projects/${id}/submissions`, {
        params: {
          submission_type: typeFilter || undefined,
          status: statusFilter || undefined,
          page,
          size
        }
      });
      setSubmissionsData(response.data);
    } catch (err: any) {
      console.error('Failed to fetch project submissions', err);
    } finally {
      setLoadingSubmissions(false);
    }
  };

  useEffect(() => {
    fetchProjectDetails();
  }, [id]);

  useEffect(() => {
    fetchSubmissions();
  }, [id, typeFilter, statusFilter, page]);

  const handleResetFilters = () => {
    setTypeFilter('');
    setStatusFilter('');
    setPage(1);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loadingProject) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-6 text-center max-w-xl mx-auto space-y-3">
        <h3 className="font-bold text-destructive">Failed to Load Project</h3>
        <p className="text-xs text-muted-foreground">{error || 'The requested project could not be found or access is restricted.'}</p>
        <Link to="/projects" className="inline-block text-xs text-primary hover:underline font-semibold">
          Back to Projects Catalog
        </Link>
      </div>
    );
  }

  // Calculate quick metrics
  const totalSubmissionsCount = submissionsData?.total || 0;
  const pasteCount = submissionsData?.items.filter(s => s.submission_type === 'paste').length || 0;
  const fileCount = submissionsData?.items.filter(s => s.submission_type === 'upload').length || 0;

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      
      {/* Header Info */}
      <div className="flex items-start gap-4 border-b border-border/40 pb-6">
        <div className="rounded-2xl bg-primary/10 p-4 border border-primary/20 text-primary">
          <Folder className="h-10 w-10" />
        </div>
        <div className="space-y-1">
          <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
            {project.name}
          </h2>
          <p className="text-sm text-muted-foreground">
            {project.description || 'No description summary saved for this project container.'}
          </p>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground pt-1.5">
            <Calendar className="h-3.5 w-3.5" />
            <span>Created on {formatDate(project.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Metrics Widgets widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-bold uppercase tracking-wider">Total Submissions</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <span className="text-3xl font-extrabold">{totalSubmissionsCount}</span>
            <Layers className="h-8 w-8 text-primary/40" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-bold uppercase tracking-wider">Pasted Snippets</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <span className="text-3xl font-extrabold">{pasteCount}</span>
            <FileCode className="h-8 w-8 text-yellow-500/40" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-bold uppercase tracking-wider">Uploaded Files</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <span className="text-3xl font-extrabold">{fileCount}</span>
            <FileSpreadsheet className="h-8 w-8 text-green-500/40" />
          </CardContent>
        </Card>
      </div>

      {/* Submissions Section */}
      <Card>
        <CardHeader className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
          <div>
            <CardTitle className="text-base font-bold">Submission History & Run Logs</CardTitle>
            <CardDescription className="text-xs">Filter and inspect security audit logs associated with this project container.</CardDescription>
          </div>

          {/* Filtering inputs */}
          <div className="flex flex-wrap gap-2 items-center">
            <div className="w-32">
              <select
                value={typeFilter}
                onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
                className="w-full text-xs py-1.5 px-2 rounded-lg border border-border bg-background"
              >
                <option value="">All Types</option>
                <option value="upload">Files</option>
                <option value="paste">Pastes</option>
              </select>
            </div>
            <div className="w-32">
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="w-full text-xs py-1.5 px-2 rounded-lg border border-border bg-background"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
            {(typeFilter || statusFilter) && (
              <Button
                variant="outline"
                onClick={handleResetFilters}
                className="text-[10px] py-1 px-2.5 h-8 flex items-center gap-1"
              >
                <span>Clear</span>
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {loadingSubmissions ? (
            <div className="flex h-32 items-center justify-center">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
            </div>
          ) : !submissionsData || submissionsData.items.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xs text-muted-foreground">No submission runs match the current criteria filters.</p>
              <div className="mt-4 flex justify-center gap-4">
                <Link to="/upload" className="text-xs text-primary hover:underline font-semibold">Upload File</Link>
                <span className="text-muted-foreground/30">|</span>
                <Link to="/paste" className="text-xs text-primary hover:underline font-semibold">Paste Snippet</Link>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Submission Logs List Table */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-border/40 text-muted-foreground uppercase font-bold tracking-wider">
                      <th className="py-2.5 px-3">Run ID</th>
                      <th className="py-2.5 px-3">Submission Type</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Date Submitted</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {submissionsData.items.map((sub) => (
                      <tr key={sub.id} className="border-b border-border/30 hover:bg-muted/10 transition-colors">
                        <td className="py-3 px-3 font-mono text-[11px] font-semibold text-foreground">
                          {sub.id.substring(0, 8)}...
                        </td>
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            sub.submission_type === 'upload' 
                              ? 'bg-green-500/10 text-green-500 border border-green-500/20' 
                              : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                          }`}>
                            {sub.submission_type === 'upload' ? 'File' : 'Paste'}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            sub.status === 'completed' 
                              ? 'bg-green-500/10 text-green-500 border border-green-500/20' 
                              : sub.status === 'failed'
                              ? 'bg-destructive/10 text-destructive border border-destructive/20'
                              : 'bg-primary/10 text-primary border border-primary/20 animate-pulse'
                          }`}>
                            {sub.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-muted-foreground">
                          {formatDate(sub.created_at)}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <Link
                            to={`/results?report=${sub.id}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                          >
                            <span>Inspect Audit</span>
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Submissions pagination controls */}
              {submissionsData.pages > 1 && (
                <div className="flex items-center justify-between border-t border-border/40 pt-4 text-[11px]">
                  <span className="text-muted-foreground">
                    Showing page <strong>{page}</strong> of <strong>{submissionsData.pages}</strong> ({submissionsData.total} runs)
                  </span>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setPage((p) => Math.max(p - 1, 1))}
                      disabled={page === 1}
                      variant="outline"
                      className="py-0.5 px-2.5 h-7 text-[10px]"
                    >
                      <ChevronLeft className="h-3 w-3" />
                    </Button>
                    <Button
                      onClick={() => setPage((p) => Math.min(p + 1, submissionsData.pages))}
                      disabled={page === submissionsData.pages}
                      variant="outline"
                      className="py-0.5 px-2.5 h-7 text-[10px]"
                    >
                      <ChevronRight className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Return prompt */}
      <div className="pt-4 text-xs">
        <Link to="/projects" className="text-muted-foreground hover:text-foreground font-semibold inline-flex items-center gap-1.5 transition-colors">
          <ChevronLeft className="h-4 w-4" />
          <span>Back to Projects list</span>
        </Link>
      </div>

    </div>
  );
};
export default ProjectDetails;
