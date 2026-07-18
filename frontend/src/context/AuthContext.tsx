import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  projects: Project[];
  activeProject: Project | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfilePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
  updateProject: (id: string, name: string, description?: string) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  selectProject: (project: Project) => void;
  refreshProjects: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  // Load state from local storage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRefreshToken = localStorage.getItem('refresh_token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setRefreshToken(storedRefreshToken);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const refreshProjects = useCallback(async () => {
    try {
      const response = await apiClient.get<{ items: Project[] }>('/projects?size=100');
      const items = response.data.items || [];
      setProjects(items);
      if (items.length > 0) {
        // Default to first project if none is active
        setActiveProject((prev) => {
          if (prev) {
            const exists = items.find((p) => p.id === prev.id);
            if (exists) return exists;
          }
          return items[0];
        });
      } else {
        setActiveProject(null);
      }
    } catch (err) {
      console.error('Failed to fetch projects list', err);
    }
  }, []);

  // Fetch projects when authenticated
  useEffect(() => {
    if (token && user) {
      refreshProjects();
    } else {
      setProjects([]);
      setActiveProject(null);
    }
  }, [token, user, refreshProjects]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token: refToken, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refToken);
      localStorage.setItem('user', JSON.stringify(userData));
      
      setToken(access_token);
      setRefreshToken(refToken);
      setUser(userData);
    } catch (err) {
      // Clear variables on failure
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setToken(null);
      setRefreshToken(null);
      setUser(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, role: string = 'Developer') => {
    setLoading(true);
    try {
      await apiClient.post('/auth/register', { email, password, role });
      // Authenticate immediately after registration
      await login(email, password);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call backend logout to invalidate refresh token in Database
      await apiClient.post('/auth/logout');
    } catch (err) {
      console.warn('Backend logout invalidation skipped or failed', err);
    } finally {
      // Clear client session tokens unconditionally
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setToken(null);
      setRefreshToken(null);
      setUser(null);
      setProjects([]);
      setActiveProject(null);
    }
  };

  const updateProfilePassword = async (currentPassword: string, newPassword: string) => {
    const response = await apiClient.put<User>('/auth/profile', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    // Profile updates that modify password trigger token rotations, force log back in or updates
    setUser(response.data);
  };

  const createProject = async (name: string, description?: string) => {
    const response = await apiClient.post<Project>('/projects', { name, description });
    await refreshProjects();
    setActiveProject(response.data);
    return response.data;
  };

  const updateProject = async (id: string, name: string, description?: string) => {
    const response = await apiClient.put<Project>(`/projects/${id}`, { name, description });
    await refreshProjects();
    setActiveProject((prev) => (prev?.id === id ? response.data : prev));
    return response.data;
  };

  const deleteProject = async (id: string) => {
    await apiClient.delete(`/projects/${id}`);
    await refreshProjects();
    setActiveProject((prev) => (prev?.id === id ? null : prev));
  };

  const selectProject = (project: Project) => {
    setActiveProject(project);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        projects,
        activeProject,
        loading,
        isAuthenticated: !!token,
        login,
        register,
        logout,
        updateProfilePassword,
        createProject,
        updateProject,
        deleteProject,
        selectProject,
        refreshProjects
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
