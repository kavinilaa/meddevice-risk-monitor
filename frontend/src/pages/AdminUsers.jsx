import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  UserCheck,
  UserX,
  AlertCircle,
  CheckCircle2,
  ShieldAlert
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { adminApi } from '../services/api';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actionMessage, setActionMessage] = useState({ type: '', text: '' });
  const [updatingId, setUpdatingId] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (roleFilter) params.role = roleFilter;
      if (statusFilter !== '') params.is_active = statusFilter === 'true';
      const res = await adminApi.getUsers(params);
      setUsers(res.data);
    } catch (err) {
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter, statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchUsers();
  };

  const handleToggleStatus = async (user) => {
    setUpdatingId(user.id);
    setActionMessage({ type: '', text: '' });
    try {
      const res = await adminApi.updateUserStatus(user.id, !user.is_active);
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: res.data.is_active } : u))
      );
      setActionMessage({
        type: 'success',
        text: `User ${user.email} is now ${res.data.is_active ? 'Active' : 'Deactivated'}.`,
      });
    } catch (err) {
      setActionMessage({
        type: 'danger',
        text: err.response?.data?.detail || 'Failed to update user status.',
      });
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header title="User Account Management" subtitle="Manage registered clinical and maintenance personnel." />

        <div className="page-body">
          {actionMessage.text && (
            <div className={`alert alert-${actionMessage.type}`} style={{ marginBottom: '1.25rem' }}>
              {actionMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
              <span>{actionMessage.text}</span>
            </div>
          )}

          {/* Filters Bar */}
          <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '260px', maxWidth: '420px' }}>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search name or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button type="submit" className="btn btn-secondary" style={{ padding: '0.65rem 1rem' }}>
                  <Search size={16} />
                </button>
              </form>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <select
                  className="form-control"
                  style={{ width: 'auto', padding: '0.45rem 2rem 0.45rem 0.75rem', fontSize: '0.85rem' }}
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                >
                  <option value="">All Roles</option>
                  <option value="BIOMEDICAL_ENGINEER">Biomedical Engineer</option>
                  <option value="MAINTENANCE_TEAM">Maintenance Team</option>
                  <option value="ADMIN">Administrator</option>
                </select>

                <select
                  className="form-control"
                  style={{ width: 'auto', padding: '0.45rem 2rem 0.45rem 0.75rem', fontSize: '0.85rem' }}
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">All Statuses</option>
                  <option value="true">Active Only</option>
                  <option value="false">Inactive Only</option>
                </select>
              </div>
            </div>
          </div>

          {/* Users Table */}
          {loading ? (
            <LoadingSpinner message="Loading user directory..." />
          ) : users.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No users registered yet"
              description="No user accounts match the current filter criteria."
            />
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>User Name</th>
                      <th>Email Address</th>
                      <th>Role</th>
                      <th>Account Status</th>
                      <th>Registered Date</th>
                      <th>Total Assessments</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td style={{ fontWeight: 700 }}>{u.full_name}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                        <td>
                          <span style={{
                            display: 'inline-block',
                            fontSize: '0.725rem',
                            fontWeight: 700,
                            padding: '0.2rem 0.5rem',
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: u.role === 'ADMIN' ? 'var(--bg-subtle)' : u.role === 'BIOMEDICAL_ENGINEER' ? 'var(--primary-50)' : 'var(--teal-50)',
                            color: u.role === 'ADMIN' ? 'var(--text-primary)' : u.role === 'BIOMEDICAL_ENGINEER' ? 'var(--primary-700)' : 'var(--teal-700)',
                            border: '1px solid var(--border-subtle)',
                          }}>
                            {u.role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : u.role === 'MAINTENANCE_TEAM' ? 'Maintenance Team' : 'Admin'}
                          </span>
                        </td>
                        <td>
                          <span style={{
                            display: 'inline-block',
                            fontSize: '0.725rem',
                            fontWeight: 700,
                            padding: '0.2rem 0.5rem',
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: u.is_active ? 'var(--risk-low-bg)' : 'var(--risk-high-bg)',
                            color: u.is_active ? 'var(--risk-low-text)' : 'var(--risk-high-text)',
                            border: `1px solid ${u.is_active ? 'var(--risk-low-border)' : 'var(--risk-high-border)'}`,
                          }}>
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.825rem', whiteSpace: 'nowrap' }}>
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td style={{ fontWeight: 700 }}>
                          {u.assessment_count}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            onClick={() => handleToggleStatus(u)}
                            disabled={updatingId === u.id}
                            className={`btn ${u.is_active ? 'btn-secondary' : 'btn-primary'}`}
                            style={{
                              fontSize: '0.775rem',
                              padding: '0.35rem 0.75rem',
                              color: u.is_active ? 'var(--risk-high-solid)' : '#ffffff',
                              borderColor: u.is_active ? 'var(--risk-high-border)' : 'transparent',
                            }}
                          >
                            {u.is_active ? <UserX size={13} /> : <UserCheck size={13} />}
                            <span>{u.is_active ? 'Deactivate' : 'Activate'}</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminUsers;
