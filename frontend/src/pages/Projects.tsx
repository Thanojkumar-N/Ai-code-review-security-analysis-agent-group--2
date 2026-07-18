import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { 
  FolderPlus, 
  Search, 
  ArrowUpDown, 
  Trash2, 
  Edit3, 
  ChevronLeft, 
  ChevronRight, 
  FolderOpen,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  FileCode
} from 'lucide-react';

interface ProjectItem {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface PaginatedProjects {
  items: ProjectItem[];
  total: int;
  page: int;
  size: int;
  pages: int;
}

export const Projects: React.FC = () => {
  const { createProject, updateProject, deleteProject, selectProject } = useAuth();
  
  // Projects State
  const [data, setData] = useState<PaginatedProjects | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Query Filters
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const size = 6; // Display 6 projects per page in grid layout

  // Modal / Form States
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedProjects>('/projects', {
        params: {
          search,
          sort_by: sortBy,
          sort_order: sortOrder,
          page,
          size
        }
      });
      setData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to retrieve project catalog list.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch whenever filters change
  useEffect(() => {
    fetchProjects();
  }, [search, sortBy, sortOrder, page]);

  // Handle Form Submission (Create or Edit)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);

    if (!name.trim()) {
      setFormError('Project name is required.');
      return;
    }

    try {
      if (editId) {
        await updateProject(editId, name, description);
        setSuccessMsg('Project updated successfully.');
      } else {
        await createProject(name, description);
        setSuccessMsg('Project created successfully.');
      }
      
      setName('');
      setDescription('');
      setEditId(null);
      setModalOpen(false);
      setPage(1); // Reset to first page
      fetchProjects();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to commit project changes.');
    }
  };

  const handleOpenEdit = (proj: ProjectItem) => {
    setEditId(proj.id);
    setName(proj.name);
    setDescription(proj.description || '');
    setFormError(null);
    setSuccessMsg(null);
    setModalOpen(true);
  };

  const handleOpenCreate = () => {
    setEditId(null);
    setName('');
    setDescription('');
    setFormError(null);
    setSuccessMsg(null);
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this project and all its code submissions? This action is irreversible.')) {
      return;
    }
    try {
      await deleteProject(id);
      fetchProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project container.');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
      
      {/* Upper header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
            Workspace Projects
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Organize code snippets and repository file uploads inside projects.
          </p>
        </div>
        
        <Button
          onClick={handleOpenCreate}
          className="flex items-center gap-2 self-start md:self-auto"
        >
          <FolderPlus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Query Filters Control Card */}
      <Card>
        <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          
          {/* Search bar */}
          <div className="md:col-span-5 relative">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Search Projects
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by name or description..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background transition-all"
              />
            </div>
          </div>

          {/* Sort By selection */}
          <div className="md:col-span-3">
            <Select
              label="Sort Attribute"
              options={[
                { value: 'created_at', label: 'Date Created' },
                { value: 'name', label: 'Project Name' }
              ]}
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            />
          </div>

          {/* Sort Order selection */}
          <div className="md:col-span-4">
            <Select
              label="Sort Direction"
              options={[
                { value: 'desc', label: 'Descending Order' },
                { value: 'asc', label: 'Ascending Order' }
              ]}
              value={sortOrder}
              onChange={(e) => { setSortOrder(e.target.value); setPage(1); }}
            />
          </div>

        </CardContent>
      </Card>

      {/* Notification status banners */}
      {successMsg && (
        <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid List of Projects */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-border/80 rounded-xl bg-card/20">
          <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground/60 mb-3" />
          <h3 className="text-sm font-bold text-foreground">No projects found</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
            Get started by creating a new project workspace container to run security audits.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.items.map((proj) => (
              <Card key={proj.id} className="hover:shadow-lg transition-all duration-300 flex flex-col justify-between border-border/60">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center justify-between gap-2">
                    <span className="truncate">{proj.name}</span>
                    <FolderOpen className="h-5 w-5 text-primary flex-shrink-0" />
                  </CardTitle>
                  <CardDescription className="line-clamp-2 h-8 pt-1 text-xs">
                    {proj.description || 'No description provided.'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0 flex flex-col gap-4">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground border-t border-border/40 pt-4">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Created: {formatDate(proj.created_at)}</span>
                  </div>
                  
                  {/* Actions buttons */}
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => handleOpenEdit(proj)}
                      className="p-2 rounded-lg border border-border bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                      title="Edit project properties"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(proj.id)}
                      className="p-2 rounded-lg border border-border bg-card hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                      title="Delete project"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                    <Link
                      to={`/projects/${proj.id}`}
                      onClick={() => selectProject(proj)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow transition-colors"
                    >
                      <span>Explore</span>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination Controls */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between border-t border-border/40 pt-4 text-xs">
              <span className="text-muted-foreground">
                Showing page <strong>{page}</strong> of <strong>{data.pages}</strong> ({data.total} total items)
              </span>
              <div className="flex gap-2">
                <Button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  variant="outline"
                  className="flex items-center gap-1 py-1 px-3 text-xs"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  <span>Prev</span>
                </Button>
                <Button
                  onClick={() => setPage((p) => Math.min(p + 1, data.pages))}
                  disabled={page === data.pages}
                  variant="outline"
                  className="flex items-center gap-1 py-1 px-3 text-xs"
                >
                  <span>Next</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Creation / Update Modal Overlays */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-card border border-border rounded-xl shadow-2xl p-6 relative animate-scale-up">
            <h3 className="text-lg font-bold text-foreground">
              {editId ? 'Modify Project Attributes' : 'Create Project Container'}
            </h3>
            <p className="text-xs text-muted-foreground mt-1 mb-4">
              Specify workspace container identifiers for source code auditing.
            </p>

            {formError && (
              <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs mb-4">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Project Identifier Name"
                id="proj-name"
                placeholder="e.g. backend-auth-microservice"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Description Notes
                </label>
                <textarea
                  placeholder="Summarize repository purpose or scope..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-sm p-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background min-h-[90px] resize-y"
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  {editId ? 'Save Changes' : 'Create Project'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
export default Projects;
