const steps = [
  {
    num: '01',
    title: 'Coarse Scan',
    color: '#00d4ff',
    icon: '📡',
    desc: 'The ROV sweeps a wide area of the seabed at regular intervals, collecting multi-frequency electromagnetic readings across the survey grid. This phase establishes the baseline EM response of the substrate and identifies statistical anomalies at low computational cost.',
  },
  {
    num: '02',
    title: 'Anomaly Detection',
    color: '#0099bb',
    icon: '⚡',
    desc: 'Onboard processing algorithms compare incoming EM signatures against known metal deposit spectral profiles. Regions exhibiting elevated or characteristic EM responses are automatically flagged as high-interest zones for focused investigation.',
  },
  {
    num: '03',
    title: 'Fine Scan',
    color: '#c9913a',
    icon: '🔬',
    desc: 'The ROV autonomously transitions to a dense, localised scan over flagged zones — increasing sampling density, expanding the active frequency range, and extending dwell time per measurement point. This delivers high-resolution subsurface EM characterisation.',
  },
  {
    num: '04',
    title: 'Sensor Fusion',
    color: '#e8b25a',
    icon: '🔀',
    desc: 'EM data is fused with simultaneous readings from the magnetic, depth, inertial (IMU), ultrasonic, and visual sensor suite. Orthogonal sensor placement ensures multi-directional coverage, while data fusion improves spatial accuracy and reduces false-positive rates.',
  },
  {
    num: '05',
    title: 'Metal-Priority Map',
    color: '#00d4ff',
    icon: '🗺️',
    desc: 'The integrated dataset is processed into a spatially referenced Metal-Priority Map — a ranked heat-map of the survey area that quantifies the likelihood and estimated strength of metal-rich deposits by zone, providing operators with actionable intelligence for follow-up sampling campaigns.',
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="how-it-works section-shell relative overflow-hidden"
      style={{ background: 'linear-gradient(180deg, #030d1f 0%, #061428 100%)' }}
    >
      {/* Background grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div className="container-app">
        {/* Header */}
        <div className="section-heading">
          <p className="section-label" style={{ marginBottom: '1rem' }}>Survey Methodology</p>
          <h2
            className="font-bold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(1.75rem, 3vw, 2.75rem)', marginBottom: '1rem' }}
          >
            Two-Stage{' '}
            <span className="gradient-text-cyan">Adaptive Scanning</span>
          </h2>
          <p className="text-[#7ab8d4]" style={{ maxWidth: '560px', margin: '0 auto', fontSize: '0.975rem', lineHeight: '1.7' }}>
            OceanAtlas combines broad-area reconnaissance with precision targeted scanning,
            guided by real-time EM anomaly detection for maximum efficiency.
          </p>
        </div>

        {/* Steps — vertical rail layout */}
        <div className="step-rail">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {steps.map((step) => (
              <div key={step.num} className="step-row">
                <div
                  className="step-node"
                  style={{ background: `linear-gradient(135deg, ${step.color}, ${step.color}80)`, boxShadow: `0 0 18px ${step.color}55` }}
                >
                  {step.num}
                </div>
                <StepCard step={step} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function StepCard({ step }) {
  return (
    <div
      className="glass-card rounded-2xl group hover:scale-[1.01] transition-all duration-300 step-card"
      style={{ borderColor: `${step.color}25` }}
    >
      <div className="step-card-content">
        <div
          className="step-card-icon"
          style={{
            background: `${step.color}15`, border: `1px solid ${step.color}30`,
          }}
        >
          {step.icon}
        </div>
        <div>
          <p style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.15em', color: step.color, marginBottom: '0.4rem', fontFamily: 'monospace' }}>
            STEP {step.num}
          </p>
          <h3
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '0.6rem' }}
          >
            {step.title}
          </h3>
          <p style={{ fontSize: '0.875rem', color: '#6a9ab5', lineHeight: '1.65' }}>{step.desc}</p>
        </div>
      </div>
    </div>
  );
}
