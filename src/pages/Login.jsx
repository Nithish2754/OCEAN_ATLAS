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
      style={{ background: 'linear-gradient(180deg, #01050f 0%, #030d1f 60%, #061428 100%)' }}
    >
      {/* Animated background */}
      <div className="absolute inset-0 topo-bg opacity-20 z-0" />
      <div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full pointer-events-none z-0"
        style={{ background: 'radial-gradient(circle, rgba(0,212,255,0.05) 0%, transparent 70%)' }}
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
          background: 'rgba(6,20,40,0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: '24px',
        }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-[#00d4ff]/10 border border-[#00d4ff]/20 flex items-center justify-center mb-4 pulse-glow">
            <Waves size={26} className="text-[#00d4ff]" />
          </div>
          <h1
            className="text-2xl font-bold text-white mb-1"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Operator Login
          </h1>
          <p className="text-[#5a8aaa] text-sm text-center">
            Sign in to access the OceanAtlas survey dashboard
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-5 px-4 py-3 rounded-xl text-sm text-red-300"
            style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}
          >
            ⚠ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {/* Email */}
          <div className="text-left">
            <label className="block text-xs font-semibold text-[#5a8aaa] uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              id="login-email"
              type="email"
              ref={emailRef}
              required
              placeholder="you@example.com"
              className="auth-input w-full rounded-xl text-white text-sm outline-none transition-all duration-200 placeholder:text-[#2a4a5f]"
              style={{
                background: 'rgba(0,212,255,0.04)',
                border: '1px solid rgba(0,212,255,0.12)',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'rgba(0,212,255,0.4)')}
              onBlur={(e) => (e.target.style.borderColor = 'rgba(0,212,255,0.12)')}
            />
          </div>

          {/* Password */}
          <div className="text-left">
            <label className="block text-xs font-semibold text-[#5a8aaa] uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                ref={passwordRef}
                required
                placeholder="••••••••"
                className="auth-input w-full pr-12 rounded-xl text-white text-sm outline-none transition-all duration-200 placeholder:text-[#2a4a5f]"
                style={{
                  background: 'rgba(0,212,255,0.04)',
                  border: '1px solid rgba(0,212,255,0.12)',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'rgba(0,212,255,0.4)')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(0,212,255,0.12)')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#3a6a85] hover:text-[#00d4ff] transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <div className="flex justify-end mt-2">
              <button
                type="button"
                className="text-xs text-[#3a6a85] hover:text-[#00d4ff] transition-colors"
              >
                Forgot password?
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            id="login-submit-btn"
            type="submit"
            disabled={loading}
            className="auth-submit w-full rounded-xl font-semibold text-[#01050f] flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
            style={{ background: 'linear-gradient(135deg, #00d4ff 0%, #0099bb 100%)' }}
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

        {/* Sign up link */}
        <p className="mt-6 text-center text-sm text-[#3a6a85]">
          Don't have an account?{' '}
          <Link to="/signup" className="text-[#00d4ff] hover:text-white font-semibold transition-colors">
            Sign up
          </Link>
        </p>

        {/* Back to home */}
        <p className="mt-4 text-center text-xs text-[#2a4a5f]">
          <Link to="/" className="hover:text-[#5a8aaa] transition-colors">
            ← Back to OceanAtlas
          </Link>
        </p>
      </div>
    </div>
  );
}
