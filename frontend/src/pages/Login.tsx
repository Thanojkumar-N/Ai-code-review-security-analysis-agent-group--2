import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Route fallback routing if requested
  const from = (location.state as any)?.from?.pathname || '/';
  const queryParams = new URLSearchParams(location.search);
  const isExpired = queryParams.get('expired') === 'true';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Authentication failed. Verify email/password credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border bg-card p-8 shadow-2xl backdrop-blur-sm transition-all duration-300">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <div className="rounded-2xl bg-primary/10 p-4 border border-primary/20">
            <ShieldAlert className="h-10 w-10 text-primary" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold tracking-tight font-sans">
            Welcome back
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to start auditing code repositories.
          </p>
        </div>

        {/* Expired Session Indicator */}
        {isExpired && (
          <div className="flex items-center gap-3 rounded-lg bg-yellow-500/10 p-3 border border-yellow-500/20 text-yellow-500 text-xs">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>Your authentication session has expired. Please sign in again.</span>
          </div>
        )}

        {/* Global Error Banner */}
        {error && (
          <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Email Address"
              id="email"
              type="email"
              placeholder="developer@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <div className="relative">
              <Input
                label="Password"
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Link 
                to="/forgot-password" 
                className="absolute right-0 top-0 text-xs text-primary hover:underline font-semibold"
              >
                Forgot password?
              </Link>
            </div>
          </div>

          <Button
            type="submit"
            isLoading={loading}
            className="w-full mt-4"
          >
            Sign In
          </Button>
        </form>

        {/* Sign up prompt links */}
        <p className="mt-8 text-center text-xs text-muted-foreground">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-semibold text-primary hover:underline"
          >
            Register workspace account
          </Link>
        </p>
      </div>
    </div>
  );
};
export default Login;
