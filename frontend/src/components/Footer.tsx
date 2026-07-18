import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-card/40 py-4 px-8 text-center text-xs text-muted-foreground">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
        <p>© {new Date().getFullYear()} AI Code Review & Security Analysis Agent. All rights reserved.</p>
        <p className="font-mono text-[10px] tracking-wide uppercase">Foundation Layer v1.0.0 (Secure Sandbox Build)</p>
      </div>
    </footer>
  );
};
export default Footer;
