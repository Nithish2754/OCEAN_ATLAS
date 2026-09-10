import { useState } from 'react';

const deposits = [
  {
    id: 'nodules',
    name: 'Polymetallic Nodules',
    icon: '⬡',
    accent: '#00d4ff',
    depth: '4,000–6,000 m',
    location: 'Clarion-Clipperton Zone, Pacific',
    image: '/images/deposit_nodules.jpg',
    description:
      'Potato-sized mineral concretions that lie loose on the abyssal seafloor, growing at a geological pace of just millimetres per million years. They form as manganese, nickel, copper, and cobalt slowly precipitate from seawater around a tiny nucleus — a shark tooth, a shell fragment — over tens of millions of years.',
    significance:
      'A primary target for the battery-metal supply chain. The Clarion-Clipperton Zone alone is estimated to contain more nickel and cobalt than all known land-based reserves combined.',
    metals: ['Manganese', 'Nickel', 'Copper', 'Cobalt'],
    metalColors: ['#00d4ff', '#c9913a', '#b87333', '#6ee7b7']},
  {
    id: 'hydrothermal',
    name: 'Hydrothermal Sulphides',
    icon: '♨',
    accent: '#ff6b35',
    depth: '500–4,000 m',
    location: 'Mid-Atlantic Ridge, SW Pacific',
    image: '/images/deposit_hydrothermal.jpg',
    description:
      'Formed at mid-ocean ridges and volcanic arcs, where superheated fluid — the iconic "black smokers" — erupts from the seafloor and instantly chills on contact with near-freezing seawater, precipitating dense metal sulphide chimneys and mounds at extraordinary speed by geological standards.',
    significance:
      'Some of the highest-grade base and precious metal deposits known to science. They also host unique chemosynthetic ecosystems, making any extraction ecologically complex and requiring careful assessment.',
    metals: ['Copper', 'Zinc', 'Lead', 'Gold', 'Silver'],
    metalColors: ['#b87333', '#e8e8e8', '#9ca3af', '#f59e0b', '#c0c0c0']},
  {
    id: 'crusts',
    name: 'Cobalt-Rich Fe-Mn Crusts',
    icon: '◧',
    accent: '#c9913a',
    depth: '800–2,500 m',
    location: 'Prime Crust Zone, Western Pacific',
    image: '/images/deposit_crusts.jpg',
    description:
      'Thin, pavement-like metallic coatings on the flanks and summits of seamounts, ridges, and underwater plateaus. Unlike the rapid formation of hydrothermal deposits, these crusts grow imperceptibly slowly from cold seawater over tens of millions of years, accumulating trace metals layer by layer.',
    significance:
      'A critical source of cobalt for lithium-ion batteries and aerospace superalloys, alongside platinum-group elements and rare earths — resources where land-based supply chains carry significant geopolitical concentration risk.',
    metals: ['Cobalt', 'Manganese', 'Iron', 'Nickel', 'Platinum (trace)', 'REEs'],
    metalColors: ['#6ee7b7', '#00d4ff', '#a1a1aa', '#c9913a', '#e8e8e8', '#a78bfa']},
  {
    id: 'ree',
    name: 'REE-Bearing Sediments',
    icon: '◈',
    accent: '#a78bfa',
    depth: '4,000–6,000 m+',
    location: 'Pacific & Indian Ocean abyssal plains',
    image: '/images/deposit_ree.jpg',
    description:
      'Deep-sea muds and clays on abyssal plains that have absorbed rare-earth elements and yttrium from seawater over geological timescales, adsorbing onto biogenic and clay-rich sediment particles. A single deposit can cover hundreds of square kilometres at shallow sediment depths.',
    significance:
      'A potential future source of rare earths critical for high-performance magnets in EV motors and wind turbines, electronics, and advanced defence systems — reducing dependence on the narrow land-based supply chain currently dominated by a handful of nations.',
    metals: ['Rare Earths (REEs)', 'Yttrium', 'Scandium'],
    metalColors: ['#a78bfa', '#c4b5fd', '#7c3aed']},
];


export default function DepositTypes() {
  const [active, setActive] = useState(0);
  const dep = deposits[active];

  return (
    <section
      id="deposits"
      className="section-shell relative overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #061428 0%, #030d1f 100%)',
        borderBottom: '1px solid rgba(0,212,255,0.09)',
      }}
    >
      {/* Background glow */}
      <div
        className="absolute bottom-0 left-0 rounded-full pointer-events-none"
        style={{
          width: '600px', height: '600px',
          background: `radial-gradient(circle, ${dep.accent}08 0%, transparent 70%)`,
          transform: 'translate(-30%, 30%)',
          transition: 'background 0.5s'}}
      />

      <div className="container-app relative z-10">
        {/* Section header */}
        <div className="section-heading">
          <p className="section-label">Target Deposit Types</p>
          <h2
            className="font-bold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(1.75rem, 3vw, 2.75rem)'}}
          >
            Four Classes of{' '}
            <span className="gradient-text-gold">Deep-Sea Metal Wealth</span>
          </h2>
          <p className="text-[#7ab8d4]" style={{ maxWidth: '600px', margin: '0 auto', fontSize: '0.975rem', lineHeight: '1.7' }}>
            The OceanAtlas system is tuned to detect and differentiate between the four primary
            categories of metal-rich seabed deposits, each with distinct EM signatures, depths,
            and mineral compositions.
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {deposits.map((d, i) => (
            <button
              key={d.id}
              id={`deposit-tab-${d.id}`}
              onClick={() => setActive(i)}
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: '999px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                background: active === i ? `linear-gradient(135deg, ${d.accent}, ${d.accent}88)` : 'transparent',
                color: active === i ? '#01050f' : '#7ab8d4',
                border: active === i ? 'none' : '1px solid rgba(0,212,255,0.2)',
                transform: active === i ? 'scale(1.05)' : 'scale(1)'}}
            >
              <span style={{ marginRight: '0.4rem' }}>{d.icon}</span>
              {d.name.split(' ').slice(0, 2).join(' ')}
            </button>
          ))}
        </div>

        {/* Active deposit card */}
        <div
          className="glass-card rounded-3xl overflow-hidden"
          style={{ borderColor: `${dep.accent}30`, transition: 'all 0.5s', marginBottom: '1.25rem' }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2">
            {/* Image */}
            <div style={{ position: 'relative', minHeight: '280px', overflow: 'hidden' }}>
              <img
                src={dep.image}
                alt={dep.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.7s', position: 'absolute', inset: 0 }}
                className="hover:scale-105"
              />
              <div
                style={{
                  position: 'absolute', inset: 0,
                  background: `linear-gradient(135deg, ${dep.accent}40 0%, transparent 60%, rgba(3,13,31,0.7) 100%)`}}
              />
              <div style={{ position: 'absolute', top: '1.5rem', left: '1.5rem' }}>
                <span
                  style={{
                    padding: '0.3rem 0.85rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700,
                    letterSpacing: '0.05em', textTransform: 'uppercase',
                    background: `${dep.accent}22`, color: dep.accent, border: `1px solid ${dep.accent}44`}}
                >
                  {dep.depth}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="deposit-content">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem'}}>
                <span style={{ fontSize: '2rem', filter: `drop-shadow(0 0 10px ${dep.accent})` }}>{dep.icon}</span>
                <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1.4rem', fontWeight: 700, color: '#fff' }}>
                  {dep.name}
                </h3>
              </div>

              <p style={{ fontSize: '0.8rem', color: '#5a8aaa', marginBottom: '0.8rem'}}>
                📍 {dep.location}
              </p>

              <p style={{ color: '#7ab8d4', lineHeight: '1.7',  fontSize: '0.95rem', marginBottom: '1rem' }}>
                {dep.description}
              </p>

              <div
                className="deposit-callout"
                style={{
                  borderRadius: '12px', marginBottom: '1rem',
                  background: `${dep.accent}08`, border: `1px solid ${dep.accent}20`}}
              >
                  <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, color: dep.accent, marginBottom: '0.5rem'}}>
                  Why It Matters
                </p>
                <p style={{ fontSize: '0.875rem', color: '#a0c4d8', lineHeight: '1.65' }}>{dep.significance}</p>
              </div>

              {/* Key metals */}
              <div>
                <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, color: '#5a8aaa', marginBottom: '0.75rem'}}>
                  Key Metals
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {dep.metals.map((metal, i) => (
                    <span
                      key={metal}
                      style={{
                        padding: '0.375rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600,
                        background: `${dep.metalColors[i] || dep.accent}15`,
                        color: dep.metalColors[i] || dep.accent,
                        border: `1px solid ${dep.metalColors[i] || dep.accent}30`}}
                    >
                      {metal}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
