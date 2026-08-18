import React, { useState } from 'react';
import { User, Lock, CheckCircle2, AlertCircle, Shield, Wrench, ShieldAlert } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../services/api';

const Profile = () => {
  const { user, updateProfile } = useAuth();

  // Name Update Form
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [nameSuccess, setNameSuccess] = useState('');
  const [nameError, setNameError] = useState('');
  const [nameLoading, setNameLoading] = useState(false);

  // Password Change Form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState('');
  const [pwdError, setPwdError] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);

  const handleUpdateName = async (e) => {
    e.preventDefault();
    setNameSuccess('');
    setNameError('');

    if (!fullName.trim()) {
      setNameError('Name cannot be empty.');
      return;
    }

    setNameLoading(true);
    try {
      const res = await userApi.updateProfile({ full_name: fullName.trim() });
      updateProfile(res.data);
      setNameSuccess('Profile updated successfully.');
    } catch (err) {
      setNameError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdSuccess('');
    setPwdError('');

    if (newPassword.length < 6) {
      setPwdError('New password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPwdError('New passwords do not match.');
      return;
    }

    setPwdLoading(true);
    try {
      await userApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      setPwdSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err) {
      setPwdError(err.response?.data?.detail || 'Failed to update password.');
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header title="User Profile & Security" subtitle="Manage your account details and credentials." />

        <div className="page-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
            {/* Account Info & Name Update Card */}
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--primary-50)',
                  color: 'var(--primary-600)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <User size={20} />
                </div>
                <div>
                  <h3 className="card-title" style={{ marginBottom: 0 }}>Account Information</h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Registered details and role access</p>
                </div>
              </div>

              {nameSuccess && (
                <div className="alert alert-info" style={{ marginBottom: '1rem' }}>
                  <CheckCircle2 size={18} />
                  <span>{nameSuccess}</span>
                </div>
              )}
              {nameError && (
                <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
                  <AlertCircle size={18} />
                  <span>{nameError}</span>
                </div>
              )}

              <form onSubmit={handleUpdateName}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-control"
                    value={user?.email || ''}
                    disabled
                    style={{ backgroundColor: 'var(--bg-app)', cursor: 'not-allowed' }}
                  />
                  <p className="form-hint">Email address cannot be changed.</p>
                </div>

                <div className="form-group">
                  <label className="form-label">Assigned Role</label>
                  <input
                    type="text"
                    className="form-control"
                    value={user?.role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : user?.role === 'MAINTENANCE_TEAM' ? 'Maintenance Team' : 'Platform Administrator'}
                    disabled
                    style={{ backgroundColor: 'var(--bg-app)', cursor: 'not-allowed' }}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Member Since</label>
                  <input
                    type="text"
                    className="form-control"
                    value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                    disabled
                    style={{ backgroundColor: 'var(--bg-app)', cursor: 'not-allowed' }}
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={nameLoading} style={{ marginTop: '0.5rem' }}>
                  {nameLoading ? 'Saving...' : 'Update Name'}
                </button>
              </form>
            </div>

            {/* Password Change Card */}
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--primary-50)',
                  color: 'var(--primary-600)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Lock size={20} />
                </div>
                <div>
                  <h3 className="card-title" style={{ marginBottom: 0 }}>Change Password</h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Securely update account credentials</p>
                </div>
              </div>

              {pwdSuccess && (
                <div className="alert alert-info" style={{ marginBottom: '1rem' }}>
                  <CheckCircle2 size={18} />
                  <span>{pwdSuccess}</span>
                </div>
              )}
              {pwdError && (
                <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
                  <AlertCircle size={18} />
                  <span>{pwdError}</span>
                </div>
              )}

              <form onSubmit={handleChangePassword}>
                <div className="form-group">
                  <label className="form-label">Current Password <span className="required">*</span></label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="Enter current password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">New Password <span className="required">*</span></label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="At least 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Confirm New Password <span className="required">*</span></label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="Re-enter new password"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={pwdLoading} style={{ marginTop: '0.5rem' }}>
                  {pwdLoading ? 'Updating Password...' : 'Change Password'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
