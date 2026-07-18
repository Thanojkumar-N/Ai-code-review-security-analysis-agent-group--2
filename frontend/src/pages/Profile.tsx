import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { User, ShieldAlert, CheckCircle2, AlertTriangle, Key } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, updateProfilePassword } = useAuth();
  
  // Password change form states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError('New password and password confirmation do not match.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    try {
      await updateProfilePassword(currentPassword, newPassword);
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update credentials. Confirm password is correct.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex h-48 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto">
      {/* Intro Header */}
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
          My Account Profile
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Review your permission scope and modify authentication settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        
        {/* Profile details */}
        <div className="md:col-span-5 space-y-6">
          <Card>
            <CardHeader className="flex flex-col items-center text-center pb-4 border-b border-border/40">
              <div className="rounded-full bg-primary/10 p-4 border border-primary/20 text-primary">
                <User className="h-12 w-12" />
              </div>
              <CardTitle className="mt-4 text-base font-extrabold">{user.email}</CardTitle>
              <CardDescription className="text-xs uppercase font-bold tracking-widest text-primary mt-1">
                {user.role} Scope
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4 text-sm">
              <div className="flex justify-between py-1 border-b border-border/30">
                <span className="text-muted-foreground text-xs">Account ID</span>
                <span className="font-mono text-xs truncate max-w-[120px] font-semibold" title={user.id}>
                  {user.id.substring(0, 8)}...
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/30">
                <span className="text-muted-foreground text-xs">Permission Role</span>
                <span className="font-semibold text-foreground">{user.role}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground text-xs">Account Status</span>
                <span className="inline-flex items-center gap-1 font-semibold text-green-500 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded-full text-[10px]">
                  <span>Active</span>
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Change password card */}
        <div className="md:col-span-7 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5 text-primary" />
                <span>Security Credentials</span>
              </CardTitle>
              <CardDescription>
                Modify your current password. Note that changing password resets active sessions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordChange} className="space-y-4">
                {success && (
                  <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
                    <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                    <span>Password updated successfully! Active sessions have been rotated.</span>
                  </div>
                )}
                {error && (
                  <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
                <Input
                  label="Current Password"
                  id="current-password"
                  type="password"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <Input
                  label="New Password"
                  id="new-password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <Input
                  label="Confirm New Password"
                  id="confirm-password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <Button type="submit" isLoading={loading} className="w-full">
                  Update Password
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
};
export default Profile;
