'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiKeysApi } from '@/lib/api';
import { Key, Plus, Trash2, Copy, Zap, Loader2, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatRelativeDate } from '@/lib/utils';
import type { APIKey } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

export default function APIKeysPage() {
  const { currentOrgId } = useAuthStore();
  const qc = useQueryClient();

  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [revealedKeyId, setRevealedKeyId] = useState<string | null>(null);

  const { data: apiKeys = [], isLoading } = useQuery({
    queryKey: ['api-keys', currentOrgId],
    queryFn: () =>
      currentOrgId
        ? apiKeysApi.list(currentOrgId).then((r) => r.data)
        : Promise.resolve([]),
    enabled: !!currentOrgId,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(currentOrgId!, { name }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['api-keys', currentOrgId] });
      setRevealedKey(res.data.key);
      setRevealedKeyId(res.data.id);
      setCreating(false);
      setNewKeyName('');
      toast.success("API key created — copy it now, it won't be shown again!");
    },
    onError: () => toast.error('Failed to create API key'),
  });

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => apiKeysApi.revoke(currentOrgId!, keyId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys', currentOrgId] });
      toast.success('API key revoked');
    },
    onError: () => toast.error('Failed to revoke API key'),
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    createMutation.mutate(newKeyName.trim());
  };

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="p-8 min-h-full" style={{ background: 'var(--bg-base)' }}>
      {/* Header */}
      <motion.div className="flex items-center justify-between mb-8"
        initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Zap size={14} className="text-violet-200" />
            <span className="text-xs font-semibold uppercase tracking-widest text-violet-200">Access Control</span>
          </div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>API Keys</h1>
          <p className="text-sm mt-0.5 text-slate-300">Manage programmatic access to your organization</p>
        </div>
        <motion.button
          onClick={() => setCreating(true)}
          whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
          className="btn-primary flex items-center gap-2">
          <Plus size={15} />
          New API Key
        </motion.button>
      </motion.div>

      {/* Create form */}
      <AnimatePresence>
        {creating && (
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12, scale: 0.98 }}
            transition={{ duration: 0.25 }}
            className="card p-6 mb-6"
            style={{ borderColor: 'rgba(167,139,250,0.25)' }}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider mb-4 text-slate-200">
              New API Key
            </h2>
            <form onSubmit={handleCreate} className="flex items-center gap-3">
              <input
                autoFocus
                type="text"
                placeholder="Key name (e.g. production-server)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="input flex-1"
                maxLength={255}
              />
              <button type="submit" disabled={!newKeyName.trim() || createMutation.isPending}
                className="btn-primary flex items-center gap-2 text-sm">
                {createMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                {createMutation.isPending ? 'Creating…' : 'Create'}
              </button>
              <button type="button" onClick={() => { setCreating(false); setNewKeyName(''); }}
                className="btn-secondary text-sm">
                <X size={14} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Revealed key banner */}
      <AnimatePresence>
        {revealedKey && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="card p-5 mb-6"
            style={{ borderColor: 'rgba(251,191,36,0.55)', background: 'rgba(251,191,36,0.09)' }}
          >
            <p className="text-xs font-bold uppercase tracking-wider mb-3 text-amber-200">
              Copy your key now - it will not be shown again
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2.5 rounded-xl text-sm font-mono break-all"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                {revealedKey}
              </code>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => copyKey(revealedKey)}
                className="btn-secondary text-sm flex items-center gap-1.5 flex-shrink-0">
                <Copy size={13} /> Copy
              </motion.button>
            </div>
            <button onClick={() => { setRevealedKey(null); setRevealedKeyId(null); }}
              className="mt-3 text-xs font-semibold text-amber-100 transition-colors hover:text-white">
              I&apos;ve saved it - dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Key list */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-5">
              <div className="flex items-center gap-3">
                <div className="skeleton w-8 h-8 rounded-xl" />
                <div>
                  <div className="skeleton h-4 w-32 rounded mb-2" />
                  <div className="skeleton h-3 w-24 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : apiKeys.length === 0 && !revealedKey ? (
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="empty-state py-20">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'var(--bg-elevated)' }}>
              <Key size={28} style={{ color: 'var(--text-muted)' }} />
            </div>
            <p className="font-semibold text-slate-200">No API keys yet</p>
            <p className="text-xs mt-1 text-slate-300">Create a key to get started with the API</p>
          </div>
        </motion.div>
      ) : (
        <motion.div
          className="space-y-3"
          initial="hidden"
          animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
        >
          {apiKeys.map((k: APIKey) => (
            <motion.div key={k.id}
              variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.35 } } }}
              className="card p-5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: k.is_active ? 'rgba(167,139,250,0.15)' : 'var(--bg-elevated)' }}>
                  <Key size={16} style={{ color: k.is_active ? 'var(--violet)' : 'var(--text-muted)' }} />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{k.name}</p>
                  <p className="text-xs font-mono mt-0.5 text-slate-300">
                    {k.key_prefix}<span className="tracking-widest">••••••••</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-5 flex-shrink-0">
                <div className="text-right hidden sm:block">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400">Created</p>
                  <p className="text-xs text-slate-200">{formatRelativeDate(k.created_at)}</p>
                </div>
                <div className="text-right hidden sm:block">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400">Last used</p>
                  <p className="text-xs text-slate-200">
                    {k.last_used_at ? formatRelativeDate(k.last_used_at) : 'Never'}
                  </p>
                </div>
                <span className={k.is_active ? 'badge-active' : 'badge-muted'}>
                  {k.is_active ? 'Active' : 'Revoked'}
                </span>
                {k.id !== revealedKeyId && k.is_active && (
                  <motion.button
                    whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      if (confirm(`Revoke key "${k.name}"? This cannot be undone.`)) {
                        revokeMutation.mutate(k.id);
                      }
                    }}
                    disabled={revokeMutation.isPending}
                    className="btn-danger p-2 rounded-xl" title="Revoke key">
                    <Trash2 size={14} />
                  </motion.button>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
