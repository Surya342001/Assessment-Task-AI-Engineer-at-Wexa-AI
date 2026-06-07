'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { ArrowRight, BarChart3, Building2, Lock, Mail, User } from 'lucide-react';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/auth';

const signUpSchema = z.object({
  full_name: z.string().min(1, 'Name is required'),
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(8, 'Min 8 characters').regex(/[A-Z]/, 'Need one uppercase').regex(/[0-9]/, 'Need one number'),
  organization_name: z.string().min(1, 'Organization name is required'),
});

type SignUpForm = z.infer<typeof signUpSchema>;

type ApiError = {
  response?: {
    data?: {
      message?: string;
      detail?: string | { message?: string };
    };
  };
};

function getErrorMessage(error: unknown) {
  const data = (error as ApiError)?.response?.data;
  if (data?.message) return data.message;
  if (typeof data?.detail === 'string') return data.detail;
  if (data?.detail?.message) return data.detail.message;
  return 'Sign up failed';
}

export default function SignUpPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<SignUpForm>({
    resolver: zodResolver(signUpSchema),
  });

  const onSubmit = async (data: SignUpForm) => {
    setLoading(true);
    try {
      const { data: tokenData } = await authApi.signUp(data);
      localStorage.setItem('access_token', tokenData.access_token);
      const { data: me } = await authApi.me();
      setAuth(me, tokenData.access_token);
      toast.success('Workspace created successfully');
      router.replace('/dashboard');
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-bg min-h-screen px-6 py-10">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="mx-auto w-full max-w-md lg:order-2">
          <div className="mb-7 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300 ring-1 ring-blue-400/20">
              <BarChart3 size={22} />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">Analytics Platform</p>
              <p className="text-sm text-slate-300">Create your organization workspace</p>
            </div>
          </div>

          <div className="card-glass p-7">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold tracking-tight text-white">Create account</h2>
              <p className="mt-1 text-sm text-slate-300">Set up a secure analytics workspace for your team.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">Full name</label>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                  <input {...register('full_name')} className="input input-with-icon" placeholder="Surya Prakash" />
                </div>
                {errors.full_name && <p className="mt-1.5 text-xs text-rose-300">{errors.full_name.message}</p>}
              </div>

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
                  <input {...register('password')} type="password" className="input input-with-icon" placeholder="Example: Demo1234!" />
                </div>
                <p className="mt-1.5 text-xs text-slate-300">Use at least 8 characters, one uppercase letter, and one number.</p>
                {errors.password && <p className="mt-1.5 text-xs text-rose-300">{errors.password.message}</p>}
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-300">Organization</label>
                <div className="relative">
                  <Building2 className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                  <input {...register('organization_name')} className="input input-with-icon" placeholder="TCPL Analytics" />
                </div>
                {errors.organization_name && <p className="mt-1.5 text-xs text-rose-300">{errors.organization_name.message}</p>}
              </div>

              <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">
                {loading ? 'Creating workspace...' : 'Create workspace'}
                {!loading && <ArrowRight size={16} />}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-300">
              Already have an account?{' '}
              <Link href="/login" className="font-medium text-blue-300 hover:text-blue-200">Sign in</Link>
            </p>
          </div>
        </section>

        <section className="hidden lg:block">
          <p className="section-label">Workspace setup</p>
          <h1 className="mt-4 max-w-xl text-5xl font-semibold tracking-tight text-white">
            Launch a focused analytics workspace in seconds.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
            The platform includes authentication, organization management, event ingestion, dashboards, alerts, API keys, and real-time updates.
          </p>
          <div className="mt-9 grid max-w-xl gap-3">
            {['Organization-aware data model', 'Secure access token workflow', 'Dashboards, alerts, and API key management'].map((item) => (
              <div key={item} className="card flex items-center gap-3 p-4 text-slate-300">
                <span className="status-dot" />
                {item}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
