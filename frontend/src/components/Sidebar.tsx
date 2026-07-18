import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Upload, 
  FileCode, 
  FileSearch, 
  BarChart4, 
  Settings, 
  LogOut, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight,
  FolderDot,
  User
} from 'lucide-react';
import Select from './ui/Select';

export const Sidebar: React.FC = () => {
  const { user, projects, activeProject, selectProject, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Projects', path: '/projects', icon: FolderDot },
    { name: 'Upload Code', path: '/upload', icon: Upload },
    { name: 'Paste Code', path: '/paste', icon: FileCode },
    { name: 'Review Results', path: '/results', icon: FileSearch },
    { name: 'Reports', path: '/reports', icon: BarChart4 },
    { name: 'Profile', path: '/profile', icon: User },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleProjectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const project = projects.find((p) => p.id === e.target.value);
    if (project) {
      selectProject(project);
      navigate('/');
    }
  };

  const projectOptions = projects.map((p) => ({
    value: p.id,
    label: p.name,
  }));

  return (
    <aside
      className={`relative flex flex-col border-r border-border bg-card transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Sidebar Header Brand Logo */}
      <div className="flex h-16 items-center gap-3 px-6 border-b border-border/50">
        <ShieldAlert className="h-6 w-6 text-primary flex-shrink-0" />
        {!collapsed && (
          <span className="font-sans font-bold text-sm tracking-wide bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
            AI CODE REVIEWER
          </span>
        )}
      </div>

      {/* Active Workspace / Project Selector */}
      {!collapsed && projects.length > 0 && (
        <div className="p-4 border-b border-border/30 bg-muted/20">
          <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <FolderDot className="h-3.5 w-3.5" />
            <span>Active Project</span>
          </div>
          <Select
            options={projectOptions}
            value={activeProject?.id || ''}
            onChange={handleProjectChange}
            className="h-9 text-xs py-1"
          />
        </div>
      )}

      {/* Nav Menu Items */}
      <nav className="flex-1 space-y-1.5 p-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-md shadow-primary/10'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`
              }
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer User logout controls */}
      <div className="p-4 border-t border-border/50 bg-muted/10">
        {!collapsed && user && (
          <div className="mb-4 px-2">
            <p className="text-xs font-bold text-foreground truncate">{user.email}</p>
            <p className="text-[10px] uppercase font-bold tracking-wider text-primary mt-0.5">
              {user.role}
            </p>
          </div>
        )}
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Toggle collapse button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute bottom-16 -right-3 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card shadow-sm hover:bg-muted text-foreground transition-colors z-20"
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>
    </aside>
  );
};
export default Sidebar;
