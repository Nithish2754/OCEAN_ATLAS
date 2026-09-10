import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, ChevronRight } from 'lucide-react';

function SonarCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animFrame;
    let rings = [];
    let particles = [];

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Initialize particles (floating dust particles)
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.5 + 0.3,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.15,
        opacity: Math.random() * 0.4 + 0.1});
    }

    let lastRing = 0;
    const centerX = () => canvas.width * 0.5;
    const centerY = () => canvas.height * 0.75;

    const draw = (ts) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Spawn rings
      if (ts - lastRing > 1200) {
        rings.push({ r: 0, opacity: 0.9, speed: 1.2 });
        lastRing = ts;
      }

      // Draw rings
      rings = rings.filter((ring) => ring.opacity > 0.01);
      rings.forEach((ring) => {
        ctx.beginPath();
        ctx.arc(centerX(), centerY(), ring.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 212, 255, ${ring.opacity})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ring.r += ring.speed;
        ring.opacity *= 0.985;
      });

      // Draw EM wave lines
      const numLines = 5;
      for (let i = 0; i < numLines; i++) {
        const xOffset = (canvas.width / (numLines + 1)) * (i + 1);
        ctx.beginPath();
        ctx.moveTo(xOffset, 0);
        for (let y = 0; y < canvas.height; y += 4) {
          const wave = Math.sin((y + ts * 0.0015 + i * 40) * 0.04) * 6;
          ctx.lineTo(xOffset + wave, y);
        }
        ctx.strokeStyle = `rgba(0, 212, 255, 0.04)`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Draw particles
      particles.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${p.opacity})`;
        ctx.fill();
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
      });

      // Scan line
      const scanY = ((ts * 0.05) % (canvas.height + 60)) - 30;
      const grad = ctx.createLinearGradient(0, scanY - 20, 0, scanY + 20);
      grad.addColorStop(0, 'rgba(0,212,255,0)');
      grad.addColorStop(0.5, 'rgba(0,212,255,0.06)');
      grad.addColorStop(1, 'rgba(0,212,255,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, scanY - 20, canvas.width, 40);

      animFrame = requestAnimationFrame(draw);
    };

    animFrame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animFrame);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 0.85 }}
    />
  );
}

export default function Hero() {
  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="home"
      className="hero-section relative flex items-center justify-center overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #01050f 0%, #030d1f 40%, #061428 70%, #0a1a2f 100%)',
        minHeight: '100vh'
      }}
    >
      {/* Hero background image with overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: 'url(/images/hero_bg.jpg)',
          opacity: 0.35}}
      />

      {/* Deep gradient overlay */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(180deg, rgba(1,5,15,0.7) 0%, rgba(1,5,15,0.3) 50%, rgba(1,5,15,0.85) 100%)'}}
      />

      {/* Topo grid overlay */}
      <div className="absolute inset-0 topo-bg opacity-20" />

      {/* Animated canvas */}
      <SonarCanvas />

      {/* Content */}
      <div className="container-hero hero-content text-center">
        <div className="hero-badge-wrap">
          <span
            className="section-label"
            style={{ padding: '0.4rem 1.25rem', borderRadius: '999px', border: '1px solid rgba(0,212,255,0.2)', background: 'rgba(0,212,255,0.05)' }}
          >
            Deep-Ocean EM Detection &amp; Mapping System
          </span>
        </div>

        <h1
          className="font-bold leading-tight gradient-text-hero"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: 'clamp(2.25rem, 6vw, 4.5rem)'}}
        >
          Mapping the Ocean Floor's
          <br />
          Hidden Metal Wealth
        </h1>

        <p
          className="text-[#7ab8d4] font-light leading-relaxed"
          style={{ fontSize: 'clamp(1rem, 2vw, 1.2rem)', maxWidth: '680px', margin: '0 auto 2.5rem' }}
        >
          A low-cost tethered ROV platform combining multi-frequency electromagnetic sensing
          with adaptive two-stage scanning to detect and map metal-rich seabed deposits —
          producing high-resolution Metal-Priority Maps for responsible deep-ocean exploration.
        </p>

        <div className="hero-actions">
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="button-control"
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #00d4ff, #0099bb)',
              color: '#01050f', fontWeight: 700, fontSize: '0.95rem',
              border: 'none', cursor: 'pointer', transition: 'transform 0.2s'}}
            id="hero-explore-btn"
            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            Explore the Technology
            <ChevronRight size={17} />
          </button>

          <Link
            to="/login"
            className="button-control"
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              borderRadius: '12px',
              border: '1px solid rgba(0,212,255,0.3)', color: '#00d4ff',
              fontWeight: 700, fontSize: '0.95rem', textDecoration: 'none',
              transition: 'background 0.2s, border-color 0.2s'}}
            id="hero-login-btn"
          >
            Operator Login
          </Link>
        </div>

        {/* Stats row */}
        <div className="hero-stats">
          {[
            { value: '4–6 km', label: 'Survey Depth' },
            { value: '2-Stage', label: 'Adaptive Scan' },
            { value: '6+', label: 'Sensor Types' },
          ].map((stat) => (
            <div key={stat.label} className="stat-item">
              <div
                className="gradient-text-cyan font-bold"
                style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '1.5rem'}}
              >
                {stat.value}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#5a8aaa', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => scrollToSection('about')}
          className="mx-auto flex flex-col items-center gap-2 text-[#00d4ff]/50 hover:text-[#00d4ff] transition-colors duration-200"
          aria-label="Scroll down"
        >
          <span className="text-xs tracking-widest uppercase font-mono">Scroll</span>
          <ArrowDown size={18} className="float-animation" />
        </button>
      </div>
    </section>
  );
}
