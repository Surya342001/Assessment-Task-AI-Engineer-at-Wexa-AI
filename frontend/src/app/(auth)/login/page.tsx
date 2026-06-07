'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { ArrowRight, BarChart3, Lock, Mail, ShieldCheck } from 'lucide-react';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/auth';

const signInSchema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type SignInForm = z.infer<typeof signInSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<SignInForm>({
    resolver: zodResolver(signInSchema),
  });

  const onSubmit = async (data: SignInForm) => {
    setLoading(true);
    try {
      const { data: tokenData } = await authApi.signIn(data);
      localStorage.setItem('access_token', tokenData.access_token);
      const { data: me } = await authApi.me();
      setAuth(me, tokenData.access_token);
      toast.success('Signed in successfully');
      router.replace('/dashboard');
    } catch {
      toast.error('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-bg min-h-screen px-6 py-10">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="hidden lg:block">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-300">
            <span className="status-dot" /> Production-grade analytics workspace
          </div>
          <h1 className="max-w-2xl text-5xl font-semibold tracking-tight text-white">
            Understand product behavior with a clear, real-time analytics command center.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
            Track events, dashboards, alerts, and access keys from one secure workspace designed for teams and evaluators.
          </p>
          <div className="mt-10 grid max-w-xl grid-cols-3 gap-4">
            {[
              ['Real-time', 'Event ingestion'],
              ['Secure', 'JWT auth flow'],
              ['Operational', 'Alerts and APIs'],
            ].map(([title, subtitle]) => (
              <div key={title} className="card p-4">
                <p className="text-lg font-semibold text-white">{title}</p>
                <p className="mt-1 text-sm text-slate-300">{subtitle}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto w-full max-w-md">
          <div className="mb-7 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300 ring-1 ring-blue-400/20">
              <BarChart3 size={22} />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">Analytics Platform</p>
              <p className="text-sm text-slate-300">Secure workspace access</p>
            </div>
          </div>

          <div className="card-glass p-7">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold tracking-tight text-white">Sign in</h2>
              <p className="mt-1 text-sm text-slate-300">Continue to your analytics dashboard.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">Email</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                  <input {...register('email')} type="email" className="input input-with-icon" placeholder="surya@company.com" />
                </div>
                {errors.email && <p className="mt-1.5 text-xs text-rose-300">{errors.email.message}</p>}
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">Password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                  <input {...register('password')} type="password" className="input input-with-icon" placeholder="Enter your password" />
                </div>
                {errors.password && <p className="mt-1.5 text-xs text-rose-300">{errors.password.message}</p>}
              </div>

              <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">
                {loading ? 'Signing in...' : 'Sign in'}
                {!loading && <ArrowRight size={16} />}
              </button>
            </form>

            <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">
              <div className="flex items-center gap-2 text-slate-300">
                <ShieldCheck size={16} className="text-emerald-300" /> Demo login
              </div>
              <p className="mt-1 font-mono text-xs text-slate-200">surya@demo.com / Demo1234!</p>
            </div>

            <p className="mt-6 text-center text-sm text-slate-300">
              New workspace?{' '}
              <Link href="/signup" className="font-medium text-blue-300 hover:text-blue-200">Create an account</Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
