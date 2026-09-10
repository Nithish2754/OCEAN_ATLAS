const techs = [
  { icon: '📶', title: 'Multi-Frequency EM Array', color: '#00d4ff', desc: 'The primary detection system sweeps multiple electromagnetic frequencies simultaneously, exploiting the distinct EM response signatures of different metallic mineral classes to discriminate between deposit types at depth.' },
  { icon: '🎥', title: 'Underwater Camera', color: '#c9913a', desc: 'High-sensitivity visual imaging provides contextual observation of the seabed, enabling operators to visually correlate EM anomalies with visible surface features, textures, and biological indicators.' },
  { icon: '🔊', title: 'Waterproof Ultrasonic Sensor', color: '#00d4ff', desc: 'Active acoustic ranging through turbid and low-visibility water provides real-time terrain mapping and obstacle detection, ensuring safe ROV navigation close to the seabed.' },
  { icon: '📐', title: 'Depth & Inertial (IMU)', color: '#e8b25a', desc: "Precision depth sensing and a 9-axis inertial measurement unit track the ROV's exact position, orientation, and motion — anchoring every sensor reading to a verified spatial coordinate." },
  { icon: '🧲', title: 'Magnetic Sensor', color: '#a78bfa', desc: 'Detects local variations in the magnetic field caused by iron-rich and ferromagnetic mineral concentrations, providing a complementary data stream to the EM array for improved detection confidence.' },
  { icon: '🛡️', title: 'Pressure-Resistant Housing', color: '#c9913a', desc: 'All electronics are encased in a cylindrical, hydrostatically rated housing engineered to withstand the extreme pressures of deep-ocean deployment, protecting the full sensor payload at depths exceeding 4,000 m.' },
];


export default function Technology() {
  return (
    <section
      id="technology"
      className="section-shell relative overflow-hidden"
      style={{ background: 'linear-gradient(180deg, #061428 0%, #030d1f 100%)' }}
    >
      {/* Background accent */}
      <div
        className="absolute top-1/2 right-0 rounded-full pointer-events-none"
        style={{ width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)', transform: 'translate(30%, -50%)' }}
      />

      <div className="container-app">
        {/* Header */}
        <div className="section-heading">
          <p className="section-label">Hardware Highlights</p>
          <h2
            className="font-bold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(1.75rem, 3vw, 2.75rem)'}}
          >
            Purpose-Built for the{' '}
            <span className="gradient-text-cyan">Abyssal Environment</span>
          </h2>
          <p className="text-[#7ab8d4]" style={{ maxWidth: '580px', margin: '0 auto', fontSize: '0.975rem', lineHeight: '1.7' }}>
            Every component of the OceanAtlas sensor suite is selected and configured for
            deep-ocean conditions — extreme pressure, near-zero visibility, and the detection
            of weak electromagnetic anomalies through metres of sediment.
          </p>
        </div>

        {/* Card grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {techs.map((tech) => (
            <div
              key={tech.title}
              className="hardware-card glass-card rounded-2xl group transition-all duration-300 hover:-translate-y-1"
            >
              {/* Top accent bar */}
              <div
                style={{
                  width: '100%', height: '2px', borderRadius: '999px',
                  background: `linear-gradient(90deg, ${tech.color}, transparent)`}}
              />
              <div
                style={{
                  width: '48px', height: '48px', borderRadius: '12px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.5rem',
                  background: `${tech.color}12`, border: `1px solid ${tech.color}25`,
                  transition: 'transform 0.2s'}}
                className="group-hover:scale-110"
              >
                {tech.icon}
              </div>
              <h3
                style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1rem', fontWeight: 700, color: tech.color, marginTop: '0.75rem', marginBottom: '0.5rem'}}
              >
                {tech.title}
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#6a9ab5', lineHeight: '1.65' }}>{tech.desc}</p>
            </div>
          ))}
        </div>

        {/* Orthogonal note */}
        <div
          style={{
            borderRadius: '16px', padding: '1.25rem 1.75rem', textAlign: 'center',
            background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.12)'}}
        >
          <span style={{ color: '#00d4ff', fontWeight: 600, fontSize: '0.875rem' }}>
            ⊕ Orthogonal Sensor Configuration
          </span>
          <p style={{ marginTop: '0.6rem', color: '#5a8aaa', fontSize: '0.875rem', maxWidth: '580px', margin: '0.6rem auto 0', lineHeight: '1.65' }}>
            Sensors are mounted in a multi-axis orthogonal arrangement, enabling simultaneous
            measurement in multiple spatial planes — ensuring full-coverage EM and magnetic field
            sampling regardless of ROV heading or terrain topology.
          </p>
        </div>
      </div>
    </section>
  );
}
