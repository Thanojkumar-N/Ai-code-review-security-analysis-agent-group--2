import React from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon, Monitor, Folder } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { activeProject } = useAuth();
  const { theme, setTheme } = useTheme();

  // Map routes to human readable titles
  const routeTitles: { [key: string]: string } = {
    '/': 'Dashboard Overview',
    '/upload': 'Upload Code Repository',
    '/paste': 'Paste Code Snippets',
    '/results': 'Code Review & Vulnerability Explorer',
    '/reports': 'Report Archives',
    '/settings': 'System Settings',
    '/profile': 'My Account Profile',
    '/projects': 'Workspace Projects Catalog',
  };

  let currentTitle = routeTitles[location.pathname] || 'AI Code Reviewer';
  if (location.pathname.startsWith('/projects/')) {
    currentTitle = 'Project Workspace Details';
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card/60 backdrop-blur-md px-8 sticky top-0 z-10">
      {/* Title / Context details */}
      <div className="flex flex-col">
        <h1 className="text-sm font-bold tracking-tight text-foreground">{currentTitle}</h1>
        {activeProject && (
          <div className="flex items-center gap-1 mt-0.5 text-xs text-muted-foreground">
            <Folder className="h-3 w-3" />
            <span>Workspace: <strong>{activeProject.name}</strong></span>
          </div>
        )}
      </div>

      {/* Theme Toggles */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/30 p-1">
          <button
            onClick={() => setTheme('light')}
            className={`rounded-md p-1.5 transition-colors ${
              theme === 'light' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Light Mode"
          >
            <Sun className="h-4 w-4" />
          </button>
          <button
            onClick={() => setTheme('dark')}
            className={`rounded-md p-1.5 transition-colors ${
              theme === 'dark' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Dark Mode"
          >
            <Moon className="h-4 w-4" />
          </button>
          <button
            onClick={() => setTheme('system')}
            className={`rounded-md p-1.5 transition-colors ${
              theme === 'system' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
            title="System Theme"
          >
            <Monitor className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
export default Navbar;
