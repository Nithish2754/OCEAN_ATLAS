import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Waves, Eye, EyeOff, ArrowRight } from 'lucide-react';

export default function Login() {
  const emailRef = useRef();
  const passwordRef = useRef();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(emailRef.current.value, passwordRef.current.value);
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.code === 'auth/invalid-credential' || err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password'
          ? 'Invalid email or password. Please try again.'
          : err.code === 'auth/too-many-requests'
          ? 'Too many failed attempts. Please try again later.'
          : 'Failed to sign in. Please check your credentials.'
      );
    }
    setLoading(false);
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center relative isolate overflow-hidden px-4"
      style={{ background: 'linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 60%, var(--bg-tertiary) 100%)' }}
    >
      {/* Animated background */}
      <div className="absolute inset-0 topo-bg opacity-20 z-0" />
      <div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none z-0"
        style={{ background: 'radial-gradient(circle, var(--border-light) 0%, transparent 70%)' }}
      />
      {/* Sonar rings */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none z-0">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute rounded-full border border-[#00d4ff]/10"
            style={{
              width: `${(i + 1) * 200}px`,
              height: `${(i + 1) * 200}px`,
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              animation: `sonar-ping ${3 + i}s ease-out infinite ${i * 1}s`,
            }}
          />
        ))}
      </div>

      <div
        className="auth-card relative z-10 w-full max-w-md"
        style={{
          background: 'var(--bg-card)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--border-medium)',
          borderRadius: '24px',
        }}
      >
        <div className="flex flex-col gap-[28px] w-full px-2 sm:px-6 py-2 sm:py-6">
          
          {/* Header Section */}
          <div className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-2 pulse-glow" style={{ background: 'var(--border-light)', border: '1px solid var(--border-medium)' }}>
              <Waves size={26} className="text-[var(--accent-cyan)]" />
            </div>
            <h1
              className="text-2xl font-bold text-[var(--text-primary)]"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              Operator Login
            </h1>
            <p className="text-[var(--text-muted)] text-sm text-center">
              Sign in to access the OceanAtlas survey dashboard
            </p>
          </div>

          {/* Error */}
          {error && (
            <div
              className="px-4 py-3 rounded-xl text-sm text-red-300"
              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              ⚠ {error}
            </div>
          )}

          {/* Form Section */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-[24px] w-full">
            
            {/* Email Field Group */}
            <div className="flex flex-col gap-[8px]">
              <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                Email Address
              </label>
              <input
                id="login-email"
                type="email"
                ref={emailRef}
                required
                placeholder="you@example.com"
                className="auth-input w-full rounded-xl text-[var(--text-primary)] text-sm outline-none transition-all duration-200 placeholder:text-[var(--text-muted)]"
                style={{
                  background: 'var(--border-light)',
                  border: '1px solid var(--border-medium)',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'var(--accent-cyan)')}
                onBlur={(e) => (e.target.style.borderColor = 'var(--border-medium)')}
              />
            </div>

            {/* Password Field Group */}
            <div className="flex flex-col gap-[8px]">
              <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  ref={passwordRef}
                  required
                  placeholder="••••••••"
                  className="auth-input w-full pr-12 rounded-xl text-[var(--text-primary)] text-sm outline-none transition-all duration-200 placeholder:text-[var(--text-muted)]"
                  style={{
                    background: 'var(--border-light)',
                    border: '1px solid var(--border-medium)',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = 'var(--accent-cyan)')}
                  onBlur={(e) => (e.target.style.borderColor = 'var(--border-medium)')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--accent-cyan)] transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              
              {/* Forgot Password */}
              <div className="flex justify-end pt-[2px]">
                <button
                  type="button"
                  className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-cyan)] transition-colors"
                >
                  Forgot password?
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              id="login-submit-btn"
              type="submit"
              disabled={loading}
              className="auth-submit w-full rounded-xl font-semibold text-[var(--bg-primary)] flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100 mt-1"
              style={{ background: 'linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-cyan-hover) 100%)' }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
                  </svg>
                  Authenticating...
                </span>
              ) : (
                <>
                  Sign In <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Footer Links Section */}
          <div className="flex flex-col items-center gap-[12px] pt-[2px]">
            <p className="text-sm text-[var(--text-muted)]">
              Don't have an account?{' '}
              <Link to="/signup" className="text-[var(--accent-cyan)] hover:text-[var(--text-primary)] font-semibold transition-colors">
                Sign up
              </Link>
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              <Link to="/" className="hover:text-[var(--text-secondary)] transition-colors">
                ← Back to OceanAtlas
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
