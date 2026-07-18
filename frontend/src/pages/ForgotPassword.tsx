import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../api/client';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { KeyRound, AlertTriangle, CheckCircle2, ArrowLeft } from 'lucide-react';

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [step, setStep] = useState<1 | 2>(1); // Step 1: Request, Step 2: Reset
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [debugToken, setDebugToken] = useState<string | null>(null);
  
  const navigate = useNavigate();

  const handleRequestToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/forgot-password', { email });
      setSuccess('Recovery instructions have been prepared. Please find your mock token below.');
      
      // Save debug token for easy sandbox copy-paste
      if (response.data.debug_token) {
        setDebugToken(response.data.debug_token);
      }
      
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to dispatch recovery request.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      setLoading(false);
      return;
    }

    try {
      await apiClient.post('/auth/reset-password', {
        email,
        token,
        new_password: newPassword,
      });

      setSuccess('Your password has been successfully reset. Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reset failed. Verify recovery token code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border bg-card p-8 shadow-2xl backdrop-blur-sm transition-all duration-300">
        
        {/* Header */}
        <div className="flex flex-col items-center text-center">
          <div className="rounded-2xl bg-primary/10 p-4 border border-primary/20">
            <KeyRound className="h-10 w-10 text-primary" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold tracking-tight font-sans">
            Reset Password
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {step === 1 
              ? 'Enter email to receive recovery instructions.' 
              : 'Enter verification token and new password.'}
          </p>
        </div>

        {/* Success Alert Banner */}
        {success && (
          <div className="flex flex-col gap-2 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
              <span className="font-semibold">{success}</span>
            </div>
            {debugToken && (
              <div className="mt-1 bg-[#0a0f1d] text-slate-100 p-2 rounded font-mono text-[11px] border border-green-500/30 break-all select-all text-center">
                Mock Recovery Token: <strong className="text-primary">{debugToken}</strong>
              </div>
            )}
          </div>
        )}

        {/* Error Alert Banner */}
        {error && (
          <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Step 1: Request recovery token form */}
        {step === 1 ? (
          <form className="mt-8 space-y-6" onSubmit={handleRequestToken}>
            <Input
              label="Registered Email Address"
              id="email"
              type="email"
              placeholder="developer@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            
            <Button type="submit" isLoading={loading} className="w-full">
              Get Recovery Token
            </Button>
          </form>
        ) : (
          /* Step 2: Reset password form */
          <form className="mt-8 space-y-6" onSubmit={handleResetPassword}>
            <div className="space-y-4">
              <Input
                label="Confirm Recovery Token"
                id="token"
                type="text"
                placeholder="Enter mock recovery code"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
              />
              <Input
                label="New Password"
                id="newPassword"
                type="password"
                placeholder="•••••••• (Min 6 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" isLoading={loading} className="w-full">
              Reset Password
            </Button>
          </form>
        )}

        {/* Navigation bottom prompts */}
        <div className="mt-6 flex justify-between text-xs font-medium">
          <Link
            to="/login"
            className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Sign In</span>
          </Link>
          
          {step === 2 && (
            <button
              onClick={() => {
                setStep(1);
                setSuccess(null);
                setError(null);
              }}
              className="text-primary hover:underline"
            >
              Re-request Token
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
export default ForgotPassword;
