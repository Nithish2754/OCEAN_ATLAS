import { Link } from 'react-router-dom';
import { Waves, ExternalLink, Mail } from 'lucide-react';

const footerLinks = [
  { label: 'Home', href: '/#home' },
  { label: 'About', href: '/#about' },
  { label: 'Deposit Types', href: '/#deposits' },
  { label: 'How It Works', href: '/#how-it-works' },
  { label: 'Technology', href: '/#technology' },
  { label: 'Login', href: '/login' },
  { label: 'Sign Up', href: '/signup' },
];


export default function Footer() {
  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <footer
      className="py-16 pb-8"
      style={{ background: '#01050f', borderTop: '1px solid rgba(0,212,255,0.08)' }}
    >
      <div className="container-app">
        {/* 3-column grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12 mb-12">
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(0,212,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Waves size={18} color="#00d4ff" />
              </div>
              <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '1.15rem', color: '#fff' }}>
                Ocean<span style={{ color: '#00d4ff' }}>Atlas</span>
              </span>
            </div>
            <p style={{ color: '#4a7a95', fontSize: '0.875rem', lineHeight: '1.7', maxWidth: '280px' }}>
              A low-cost tethered ROV system for deep-ocean electromagnetic detection and
              Metal-Priority Mapping of seabed mineral deposits.
            </p>
          </div>

          {/* Nav links */}
          <div>
            <p style={{ color: '#fff', fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1.25rem' }}>
              Navigation
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {footerLinks.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith('/#') ? (
                    <button
                      onClick={() => scrollTo(link.href.replace('/#', ''))}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4a7a95', fontSize: '0.875rem', padding: 0, textAlign: 'left', transition: 'color 0.2s' }}
                      onMouseEnter={e => e.target.style.color = '#00d4ff'}
                      onMouseLeave={e => e.target.style.color = '#4a7a95'}
                    >
                      {link.label}
                    </button>
                  ) : (
                    <Link
                      to={link.href}
                      style={{ color: '#4a7a95', fontSize: '0.875rem', textDecoration: 'none', transition: 'color 0.2s' }}
                      onMouseEnter={e => e.target.style.color = '#00d4ff'}
                      onMouseLeave={e => e.target.style.color = '#4a7a95'}
                    >
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <p style={{ color: '#fff', fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1.25rem' }}>
              Project Contact
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <a
                href="mailto:contact@oceanatlas.research"
                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#4a7a95', fontSize: '0.875rem', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={e => { e.currentTarget.style.color = '#00d4ff'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#4a7a95'; }}
              >
                <Mail size={15} />
                contact@oceanatlas.research
              </a>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#4a7a95', fontSize: '0.875rem', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={e => { e.currentTarget.style.color = '#00d4ff'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#4a7a95'; }}
              >
                <ExternalLink size={15} />
                Research Repository
              </a>
              <div style={{ padding: '0.75rem 1rem', borderRadius: '10px', fontSize: '0.8rem', color: '#3a6a85', lineHeight: '1.5', background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.08)', marginTop: '0.25rem' }}>
                🎓 Academic research project. Institutional affiliation placeholder.
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div
          style={{
            paddingTop: '1.75rem',
            borderTop: '1px solid rgba(0,212,255,0.06)',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <p style={{ color: '#2a4a5f', fontSize: '0.8rem' }}>
            © 2026 OceanAtlas Research Project. All rights reserved.
          </p>
          <p style={{ color: '#2a4a5f', fontSize: '0.8rem' }}>
            Built for deep-ocean metal detection &amp; mapping research.
          </p>
        </div>
      </div>
    </footer>
  );
}
