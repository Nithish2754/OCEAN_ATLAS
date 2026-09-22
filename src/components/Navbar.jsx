import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Waves, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const navLinks = [
  { label: 'Home', href: '/#home' },
  { label: 'About', href: '/#about' },
  { label: 'Deposits', href: '/#deposits' },
  { label: 'Technology', href: '/#technology' },
];

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { currentUser } = useAuth();
  const { isLight, toggleTheme } = useTheme();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 30);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (href) => {
    setMenuOpen(false);
    if (href.startsWith('/#')) {
      const id = href.replace('/#', '');
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        transition: 'all 0.3s',
        background: isScrolled ? 'var(--bg-card)' : 'transparent',
        backdropFilter: isScrolled ? 'blur(20px)' : 'none',
        borderBottom: isScrolled ? '1px solid var(--border-light)' : 'none',
      }}
    >
      <div className="container-app h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          to="/"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <div
            style={{
              width: '36px', height: '36px', borderRadius: '50%',
              background: 'var(--border-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Waves size={18} color="var(--accent-cyan)" />
          </div>
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '1.2rem', color: 'var(--text-primary)' }}>
            Ocean<span style={{ color: 'var(--accent-cyan)' }}>Atlas</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }} className="hidden md:flex">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => handleNavClick(link.href)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 500,
                transition: 'color 0.2s',
              }}
              onMouseEnter={e => e.target.style.color = 'var(--accent-cyan)'}
              onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Auth buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }} className="hidden md:flex">
          <button onClick={toggleTheme} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0.5rem', display: 'flex', alignItems: 'center' }}>
            {isLight ? <Moon size={20} /> : <Sun size={20} />}
          </button>
          {currentUser ? (
            <Link
              to="/dashboard"
              style={{
                padding: '0.5rem 1.25rem', borderRadius: '8px',
                background: 'var(--border-light)', border: '1px solid var(--border-medium)',
                color: 'var(--accent-cyan)', fontSize: '0.875rem', fontWeight: 600, textDecoration: 'none',
              }}
            >
              Dashboard
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500, textDecoration: 'none', padding: '0.5rem 0.75rem' }}
              >
                Login
              </Link>
              <Link
                to="/signup"
                style={{
                  padding: '0.5rem 1.25rem', borderRadius: '8px',
                  background: 'var(--accent-cyan)',
                  color: 'var(--bg-primary)', fontSize: '0.875rem', fontWeight: 700, textDecoration: 'none',
                }}
              >
                Sign Up
              </Link>
            </>
          )}
        </div>

        {/* Mobile toggle */}
        <div className="md:hidden flex items-center gap-2">
          <button onClick={toggleTheme} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0.5rem' }}>
            {isLight ? <Moon size={20} /> : <Sun size={20} />}
          </button>
          <button
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-cyan)', padding: '0.5rem' }}
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div
          className="px-6 py-4 flex flex-col gap-4"
          style={{
            background: 'var(--bg-card)', backdropFilter: 'blur(20px)',
            borderBottom: '1px solid var(--border-light)',
          }}
        >
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => handleNavClick(link.href)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.95rem', padding: '0.25rem 0' }}
            >
              {link.label}
            </button>
          ))}
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {currentUser ? (
              <Link to="/dashboard" onClick={() => setMenuOpen(false)} style={{ textAlign: 'center', padding: '0.625rem', borderRadius: '8px', background: 'var(--border-light)', border: '1px solid var(--border-medium)', color: 'var(--accent-cyan)', fontWeight: 600, textDecoration: 'none' }}>
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" onClick={() => setMenuOpen(false)} style={{ color: 'var(--text-secondary)', fontWeight: 500, textDecoration: 'none' }}>Login</Link>
                <Link to="/signup" onClick={() => setMenuOpen(false)} style={{ textAlign: 'center', padding: '0.625rem', borderRadius: '8px', background: 'var(--accent-cyan)', color: 'var(--bg-primary)', fontWeight: 700, textDecoration: 'none' }}>
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
