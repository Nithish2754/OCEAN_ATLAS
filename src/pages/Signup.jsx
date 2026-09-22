import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Waves, Eye, EyeOff, ArrowRight, Check, X } from 'lucide-react';

function PasswordStrength({ password }) {
  const checks = [
    { label: 'At least 8 characters', valid: password.length >= 8 },
    { label: 'Uppercase letter', valid: /[A-Z]/.test(password) },
    { label: 'Number', valid: /[0-9]/.test(password) },
  ];
  if (!password) return null;
  return (
    <div className="mt-2 flex flex-col gap-1">
      {checks.map((c) => (
        <div key={c.label} className="flex items-center gap-2">
          {c.valid ? (
            <Check size={11} className="text-green-400" />
          ) : (
            <X size={11} className="text-[var(--text-muted)]" />
          )}
          <span className={`text-xs ${c.valid ? 'text-green-400' : 'text-[var(--text-muted)]'}`}>
            {c.label}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function Signup() {
  const nameRef = useRef();
  const emailRef = useRef();
  const passwordRef = useRef();
  const confirmRef = useRef();
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const name = nameRef.current.value.trim();
    const email = emailRef.current.value.trim();
    const pwd = passwordRef.current.value;
    const confirm = confirmRef.current.value;

    if (pwd !== confirm) return setError('Passwords do not match.');
    if (pwd.length < 8) return setError('Password must be at least 8 characters.');
    if (!name) return setError('Full name is required.');

    setLoading(true);
    try {
      await signup(email, pwd, name);
      navigate('/login');
    } catch (err) {
      setError(
        err.code === 'auth/email-already-in-use'
          ? 'An account with this email already exists.'
          : err.code === 'auth/invalid-email'
          ? 'Please enter a valid email address.'
          : err.code === 'auth/weak-password'
          ? 'Password is too weak. Use at least 8 characters.'
          : 'Failed to create account. Please try again.'
      );
    }
    setLoading(false);
  }

  const inputStyle = {
    background: 'var(--border-light)',
    border: '1px solid var(--border-medium)',
  };
  const onFocus = (e) => (e.target.style.borderColor = 'var(--accent-cyan)');
  const onBlur = (e) => (e.target.style.borderColor = 'var(--border-medium)');
  const inputCls = 'auth-input w-full rounded-xl text-[var(--text-primary)] text-sm outline-none transition-all duration-200 placeholder:text-[var(--text-muted)]';

  return (
    <div
      className="min-h-screen flex items-center justify-center relative isolate overflow-hidden px-4 py-12"
      style={{ background: 'linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 60%, var(--bg-tertiary) 100%)' }}
    >
      <div className="absolute inset-0 topo-bg opacity-20 z-0" />
      <div
        className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full pointer-events-none z-0"
        style={{ background: 'radial-gradient(circle, rgba(201,145,58,0.04) 0%, transparent 70%)' }}
      />

      <div
        className="auth-card relative z-10 w-full max-w-md"
        style={{
          background: 'var(--bg-card)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--border-medium)',
          borderRadius: '24px',
        }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--border-light)', border: '1px solid var(--border-medium)' }}>
            <Waves size={26} className="text-[var(--accent-gold)]" />
          </div>
          <h1
            className="text-2xl font-bold text-[var(--text-primary)] mb-1"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Request Access
          </h1>
          <p className="text-[var(--text-muted)] text-sm text-center">
            Create your OceanAtlas researcher account
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
          <div className="text-left">
            <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Full Name
            </label>
            <input
              id="signup-name"
              type="text"
              ref={nameRef}
              required
              placeholder="Dr. Jane Smith"
              className={inputCls}
              style={inputStyle}
              onFocus={onFocus}
              onBlur={onBlur}
            />
          </div>

          {/* Email */}
          <div className="text-left">
            <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              id="signup-email"
              type="email"
              ref={emailRef}
              required
              placeholder="you@institution.edu"
              className={inputCls}
              style={inputStyle}
              onFocus={onFocus}
              onBlur={onBlur}
            />
          </div>

          {/* Password */}
          <div className="text-left">
            <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                ref={passwordRef}
                required
                placeholder="••••••••"
                className={`${inputCls} pr-12`}
                style={inputStyle}
                onFocus={onFocus}
                onBlur={onBlur}
                onChange={(e) => setPassword(e.target.value)}
                value={password}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--accent-cyan)] transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <PasswordStrength password={password} />
          </div>

          <div className="text-left">
            <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Confirm Password
            </label>
            <input
              id="signup-confirm-password"
              type="password"
              ref={confirmRef}
              required
              placeholder="••••••••"
              className={inputCls}
              style={inputStyle}
              onFocus={onFocus}
              onBlur={onBlur}
            />
          </div>

          {/* Submit */}
          <button
            id="signup-submit-btn"
            type="submit"
            disabled={loading}
            className="auth-submit w-full rounded-xl font-semibold text-[var(--bg-primary)] flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
            style={{ background: 'linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-gold-hover, #e8b25a) 100%)' }}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
                </svg>
                Creating account...
              </span>
            ) : (
              <>
                Create Account <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
          Already have an account?{' '}
          <Link to="/login" className="text-[var(--accent-cyan)] hover:text-[var(--text-primary)] font-semibold transition-colors">
            Sign in
          </Link>
        </p>
        <p className="mt-4 text-center text-xs text-[var(--text-muted)]">
          <Link to="/" className="hover:text-[var(--text-secondary)] transition-colors">
            ← Back to OceanAtlas
          </Link>
        </p>
      </div>
    </div>
  );
}
