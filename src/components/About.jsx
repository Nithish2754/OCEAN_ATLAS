import { AlertTriangle, DollarSign, Eye } from 'lucide-react';

const problems = [
  {
    icon: <Eye size={22} className="text-[var(--accent-cyan)]" />,
    title: 'Invisible at Depth',
    desc: 'The deep seafloor lies 4–6 kilometres below the surface, shrouded in darkness, crushing pressure, and thick sediment cover. Conventional optical and acoustic methods fail to reliably detect sub-surface metal-rich formations.'},
  {
    icon: <DollarSign size={22} className="text-[var(--accent-gold)]" />,
    title: 'Prohibitively Expensive',
    desc: 'Traditional deep-ocean surveys demand large research vessels and specialised robotic platforms — assets that cost millions per deployment day and are accessible only to well-funded governmental or industrial programmes.'},
  {
    icon: <AlertTriangle size={22} className="text-[var(--accent-cyan)]" />,
    title: 'Strategically Critical',
    desc: 'The battery metals, rare earths, and precious metals locked in deep-sea deposits are essential for clean energy and high-tech supply chains. The inability to survey and quantify them is a strategic and economic blind spot.'},
];


export default function About() {
  return (
    <section
      id="about"
      className="section-shell relative overflow-hidden"
      style={{ background: 'linear-gradient(180deg, var(--bg-panel) 0%, var(--bg-tertiary) 100%)' }}
    >
      {/* Background glow */}
      <div
        className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none"
        style={{ background: `radial-gradient(circle, var(--border-light) 0%, transparent 70%)`, transform: 'translate(30%, -30%)' }}
      />

      <div className="container-app">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Left: text */}
          <div>
            <p className="section-label" style={{ marginBottom: '0.8rem' }}>The Problem</p>
            <h2
              className="font-bold text-[var(--text-primary)] leading-tight"
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: 'clamp(1.75rem, 3vw, 2.75rem)',
                marginBottom: '0.9rem'}}
            >
              The Ocean Floor Holds
              <span className="gradient-text-cyan"> Immense Wealth</span> —<br />
              And It Remains{' '}
              <span className="gradient-text-gold">Almost Unmapped</span>
            </h2>
            <p className="text-[var(--text-accent)] leading-relaxed" style={{ fontSize: '0.975rem', marginBottom: '0.8rem' }}>
              Polymetallic nodules, hydrothermal sulphide deposits, cobalt-rich crusts, and
              rare-earth sediments are distributed across vast stretches of the abyssal seafloor.
              Together they represent some of the largest untapped reserves of battery metals,
              rare earths, and precious metals on the planet.
            </p>
            <p className="text-[var(--text-accent)] leading-relaxed" style={{ fontSize: '0.975rem', margin: 0 }}>
              The <span className="text-[var(--accent-cyan)] font-medium">OceanAtlas system</span> addresses
              this gap: a low-cost, rapidly deployable tethered ROV equipped with a multi-frequency
              electromagnetic sensing array and adaptive two-stage scanning intelligence — making
              deep-ocean metal detection accessible beyond the elite tier of ocean research.
            </p>
          </div>

          {/* Right: problem cards */}
          <div className="card-stack">
            {problems.map((p) => (
              <div
                key={p.title}
                className="problem-card glass-card rounded-2xl transition-all duration-300 group hover:translate-x-1 flex gap-4 items-start"
              >
                <div
                  className="rounded-xl bg-[var(--bg-panel)] flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-200"
                  style={{ width: '44px', height: '44px', minWidth: '44px' }}
                >
                  {p.icon}
                </div>
                <div>
                  <h3
                    className="text-[var(--text-primary)] font-semibold"
                    style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1rem'}}
                  >
                    {p.title}
                  </h3>
                  <p className="text-[var(--text-muted)] leading-relaxed" style={{ fontSize: '0.85rem' }}>
                    {p.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
