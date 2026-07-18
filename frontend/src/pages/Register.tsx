import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { UserPlus, AlertTriangle } from 'lucide-react';

export const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Developer');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const roleOptions = [
    { value: 'Developer', label: 'Developer (Audit Code Submissions)' },
    { value: 'Admin', label: 'Admin (System Configuration)' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      setLoading(false);
      return;
    }

    try {
      await register(email, password, role);
      navigate('/');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Registration failed. Try again with a different email.'
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
            <UserPlus className="h-10 w-10 text-primary" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold tracking-tight font-sans">
            Create Account
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Register a profile to deploy automated security code checks.
          </p>
        </div>

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
            <Input
              label="Password"
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Select
              label="Workspace Access Role"
              id="role"
              options={roleOptions}
              value={role}
              onChange={(e) => setRole(e.target.value)}
            />
          </div>

          <Button
            type="submit"
            isLoading={loading}
            className="w-full mt-4"
          >
            Create Profile
          </Button>
        </form>

        {/* Log in prompt links */}
        <p className="mt-8 text-center text-xs text-muted-foreground">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-primary hover:underline"
          >
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
};
export default Register;
