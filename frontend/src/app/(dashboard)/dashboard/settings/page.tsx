'use client';

import { useAuthStore } from '@/store/auth';
import { User, Building2, Zap, Copy, Shield } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { user, currentOrgId } = useAuthStore();

  const copy = (val: string, label: string) => {
    navigator.clipboard.writeText(val);
    toast.success(`${label} copied`);
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() ?? '??';

  return (
    <div className="p-8 min-h-full" style={{ background: 'var(--bg-base)' }}>
      {/* Header */}
      <motion.div className="mb-8"
        initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div className="flex items-center gap-2 mb-1">
          <Zap size={14} style={{ color: 'var(--text-secondary)' }} />
          <span className="text-xs font-semibold uppercase tracking-widest text-cyan-200">Configuration</span>
        </div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Settings</h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>Manage your account and organization</p>
      </motion.div>

      <div className="max-w-2xl space-y-5">
        {/* Profile Card */}
        <motion.div className="card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.4 }}>
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(34,211,238,0.1)' }}>
              <User size={14} style={{ color: 'var(--cyan)' }} />
            </div>
            <h2 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Profile</h2>
          </div>

          <div className="flex items-center gap-4 mb-5 p-4 rounded-xl" style={{ background: 'var(--bg-elevated)' }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-sm"
              style={{ background: 'linear-gradient(135deg, #0891b2, #7c3aed)', color: '#fff' }}>
              {initials}
            </div>
            <div>
              <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{user?.full_name || '—'}</p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user?.email || '—'}</p>
            </div>
          </div>

          <div className="space-y-3">
            {[
              { label: 'Full Name', value: user?.full_name || '—' },
              { label: 'Email', value: user?.email || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-2.5 px-3 rounded-xl"
                style={{ borderBottom: '1px solid var(--border)' }}>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">{label}</span>
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{value}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Organization Card */}
        <motion.div className="card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.4 }}>
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(167,139,250,0.1)' }}>
              <Building2 size={14} style={{ color: 'var(--violet)' }} />
            </div>
            <h2 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Organization</h2>
          </div>

          <div className="py-2.5 px-3 rounded-xl" style={{ borderBottom: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs font-semibold uppercase tracking-wider flex-shrink-0 text-slate-300">
                Org ID
              </span>
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono text-xs truncate" style={{ color: 'var(--text-primary)' }}>
                  {currentOrgId || '—'}
                </span>
                {currentOrgId && (
                  <motion.button
                    whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                    onClick={() => copy(currentOrgId, 'Org ID')}
                    className="flex-shrink-0 p-1 rounded-lg text-slate-300 transition-colors hover:text-white">
                    <Copy size={13} />
                  </motion.button>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Security notice */}
        <motion.div className="card p-4 flex items-start gap-3"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.4 }}
          style={{ borderColor: 'rgba(34,211,238,0.12)', background: 'rgba(34,211,238,0.03)' }}>
          <Shield size={16} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--cyan)' }} />
          <div>
            <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Secure by default</p>
            <p className="text-xs mt-0.5 text-slate-300">
              All data is encrypted in transit and at rest. API keys are hashed and never stored in plain text.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
