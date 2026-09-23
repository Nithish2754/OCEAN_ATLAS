import React from 'react';

const DetectionSummary = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="glass-card rounded-2xl border border-[var(--border-light)] overflow-hidden flex flex-col mb-6 box-border w-full">
      {/* 
        ==================================================
        THE OUTER PADDING CONTAINER 
        ==================================================
      */}
      <div 
        className="w-full box-border" 
        style={{ padding: '20px 28px 24px 28px' }}
      >
        <div className="pb-2 flex items-center gap-3 w-full box-border">
          <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent-cyan)] animate-pulse"></span>
          <h3 className="font-bold text-lg text-[var(--text-primary)] tracking-wide" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Detection Summary
          </h3>
        </div>
        
        {/* 
          ==================================================
          THE NEW VISIBLE INNER BOX 
          ==================================================
        */}
        <div className="mt-4 border border-[var(--border-light)] rounded-xl bg-white overflow-hidden shadow-sm box-border w-full">
          <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-6 w-full box-border">
            {Object.entries(summary.classes).map(([className, count]) => (
              <div key={className} className="bg-white border border-[var(--border-light)] rounded-xl p-5 flex flex-col justify-center items-center text-center hover:border-[var(--accent-cyan)]/50 transition-colors shadow-sm">
                <span className="text-[var(--text-muted)] text-xs uppercase tracking-wider mb-2 font-medium">{className}</span>
                <span className="text-3xl font-light text-[var(--accent-cyan)]">{count}</span>
              </div>
            ))}
            
            <div className="bg-[var(--accent-cyan)]/10 border border-[var(--accent-cyan)]/30 rounded-xl p-5 flex flex-col justify-center items-center text-center hover:border-[var(--accent-cyan)] transition-colors shadow-sm">
              <span className="text-[var(--accent-cyan)] text-xs uppercase tracking-wider mb-2 font-medium">Total Detections</span>
              <span className="text-3xl font-bold text-[var(--accent-cyan)]">{summary.total_detections}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetectionSummary;
