import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import Footer from './Footer';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground transition-colors duration-300">
      {/* Sidebar navigation panel */}
      <Sidebar />

      {/* Main dashboard content container */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <Navbar />

        {/* Scrollable workspace content */}
        <main className="flex-1 overflow-y-auto px-8 py-6 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>

        {/* Footer info panel */}
        <Footer />
      </div>
    </div>
  );
};
export default DashboardLayout;
