const impacts = [
  { icon: '💰', metric: '~90%', label: 'Cost Reduction', color: '#c9913a', desc: 'A tethered ROV platform eliminates the need for multi-million-dollar specialised survey vessels. OceanAtlas brings deep-ocean metal detection within reach of university research groups and exploration startups.' },
  { icon: '⚡', metric: '10×', label: 'Faster Deployment', color: '#00d4ff', desc: 'Conventional survey campaigns require weeks of vessel mobilisation and permitting. The compact, rapidly deployable OceanAtlas system can be mission-ready and in the water within hours.' },
  { icon: '📊', metric: 'Data-First', label: 'Responsible Exploration', color: '#6ee7b7', desc: 'By generating comprehensive Metal-Priority Maps before any physical disturbance, OceanAtlas enables evidence-based extraction decisions — minimising ecological footprint and supporting regulatory compliance.' },
  { icon: '🌐', metric: 'Scalable', label: 'Fleet Deployable', color: '#a78bfa', desc: 'The modular, low-cost platform architecture allows multiple units to be deployed in parallel across wide survey areas, dramatically increasing the coverage achievable per expedition.' },
];


export default function Impact() {
  return (
    <section
      id="impact"
      className="section-shell relative overflow-hidden"
      style={{ background: 'linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-tertiary) 80%, var(--bg-panel) 100%)' }}
    >
      {/* Watermark */}
      <div
        className="absolute inset-0 flex items-center justify-center pointer-events-none select-none overflow-hidden"
        aria-hidden="true"
      >
        <span
          style={{ fontSize: '20vw', fontWeight: 900, color: 'var(--accent-cyan)', opacity: 0.015, lineHeight: 1, fontFamily: "'Space Grotesk', sans-serif" }}
        >
          IMPACT
        </span>
      </div>

      <div className="container-app relative z-10">
        {/* Header */}
        <div className="section-heading">
          <p className="section-label">Why It Matters</p>
          <h2
            className="font-bold text-[var(--text-primary)]"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(1.75rem, 3vw, 2.75rem)'}}
          >
            Democratising{' '}
            <span className="gradient-text-gold">Deep-Ocean Exploration</span>
          </h2>
          <p className="text-[var(--text-accent)]" style={{ maxWidth: '560px', margin: '0 auto', fontSize: '0.975rem', lineHeight: '1.7' }}>
            OceanAtlas doesn't just detect metal — it fundamentally changes who can explore
            the deep ocean and how responsibly they can do it.
          </p>
        </div>

        {/* Impact cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          {impacts.map((item) => (
            <div
              key={item.label}
              className="impact-card glass-card rounded-2xl text-center group hover:-translate-y-1 transition-all duration-300"
              style={{ borderColor: `${item.color}20` }}
            >
              <div
                style={{
                  width: '56px', height: '56px', borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.5rem', margin: '0 auto 1.25rem',
                  background: `${item.color}12`, border: `1px solid ${item.color}30`,
                  transition: 'transform 0.2s'}}
                className="group-hover:scale-110"
              >
                {item.icon}
              </div>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1.75rem', fontWeight: 700, color: item.color}}>
                {item.metric}
              </div>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem'}}>{item.label}</div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.65' }}>{item.desc}</p>
            </div>
          ))}
        </div>

        {/* CTA Banner */}
        <div
          className="rounded-3xl topo-bg"
          style={{
            padding: 'clamp(2rem, 4vw, 3.5rem)',
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            background: 'linear-gradient(135deg, color-mix(in srgb, var(--accent-cyan) 7%, transparent) 0%, color-mix(in srgb, var(--accent-gold) 5%, transparent) 100%)',
            border: '1px solid var(--border-medium)'}}
        >
          <h3
            className="font-bold text-[var(--text-primary)]"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(1.5rem, 3vw, 2.25rem)'}}
          >
            Ready to Map the{' '}
            <span className="gradient-text-cyan">Abyssal Unknown?</span>
          </h3>
          <p style={{ color: 'var(--text-accent)',  maxWidth: '500px', margin: '0 auto 2rem', fontSize: '0.975rem', lineHeight: '1.7' }}>
            Request operator access to the OceanAtlas survey dashboard and begin
            planning your deep-ocean EM detection campaign.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'center' }}>
            <a
              href="/signup"
              id="impact-signup-btn"
              style={{
                padding: '0.875rem 2rem', borderRadius: '12px', fontWeight: 700,
                background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-cyan-hover))',
                color: 'var(--bg-primary)', textDecoration: 'none', fontSize: '0.95rem',
                transition: 'transform 0.2s'}}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              Get Operator Access
            </a>
            <a
              href="/login"
              id="impact-login-btn"
              style={{
                padding: '0.875rem 2rem', borderRadius: '12px', fontWeight: 700,
                border: '1px solid var(--border-medium)', color: 'var(--accent-cyan)',
                textDecoration: 'none', fontSize: '0.95rem', transition: 'background 0.2s'}}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--border-light)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              Sign In
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
