import React from 'react';
import { Download, Trash2 } from 'lucide-react';

const DetectionHistory = ({ history, onReset, onGenerateReport, onDelete }) => {
  if (!history) return null;

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
        
        {/* Header / Button Area (stays outside the inner box) */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 w-full box-border pb-2">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent-cyan)] animate-pulse"></span>
            <h3 className="font-bold text-lg text-[var(--text-primary)] tracking-wide" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Detection History
            </h3>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={onReset}
              className="px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--border-light)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-light)] rounded-lg text-sm transition-colors font-medium"
            >
              Reset Session
            </button>
            
            <button 
              onClick={onGenerateReport}
              className="px-4 py-2 bg-[var(--accent-cyan)]/10 hover:bg-[var(--accent-cyan)]/20 text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30 rounded-lg text-sm transition-colors flex items-center gap-2 font-medium"
            >
              <Download size={16} />
              Generate PDF
            </button>
          </div>
        </div>
        
        {/* 
          ==================================================
          THE NEW VISIBLE INNER BOX 
          ==================================================
        */}
        <div className="mt-4 border border-[var(--border-light)] rounded-xl bg-white overflow-hidden shadow-sm box-border w-full">
          
          {history.length === 0 ? (
            <div className="text-center py-16 m-4 text-[var(--text-muted)] border border-dashed border-[var(--border-light)] rounded-lg">
              No detections recorded in this session.
            </div>
          ) : (
            <div className="w-full overflow-x-auto box-border" style={{ padding: '4px 16px 16px 16px' }}>
              <div className="w-full box-border min-w-[760px]">
                
                {/* Inner Table Header Row */}
                <div className="grid grid-cols-[100px_minmax(240px,1fr)_160px_160px_60px] gap-6 w-full items-center border-b border-[var(--border-light)] pb-4 pt-4 mb-2 text-[var(--text-muted)] text-xs uppercase tracking-wider font-semibold box-border">
                  <div>Evidence</div>
                  <div>Class</div>
                  <div>Confidence</div>
                  <div>Time</div>
                  <div className="text-right pr-2">Actions</div>
                </div>

                {/* Inner Table Data Rows */}
                <div className="flex flex-col w-full box-border">
                  {history.map((det) => (
                    <div 
                      key={det.id} 
                      className="grid grid-cols-[100px_minmax(240px,1fr)_160px_160px_60px] gap-6 w-full items-center border-b border-[var(--border-light)] py-4 hover:bg-[var(--bg-secondary)] transition-colors group rounded-md box-border"
                    >
                      {/* Column 1: Evidence */}
                      <div>
                        <img 
                          src={`http://localhost:8000/api/detections/evidence/${det.image_filename}`}
                          alt={det.class_name}
                          className="w-24 h-16 object-cover rounded-lg border border-[var(--border-light)] shadow-sm"
                          onError={(e) => { e.target.style.display = 'none' }}
                        />
                      </div>
                      
                      {/* Column 2: Class */}
                      <div className="text-[var(--text-primary)] font-medium">
                        {det.class_name}
                      </div>
                      
                      {/* Column 3: Confidence */}
                      <div className="text-green-400 font-medium">
                        {det.confidence}%
                      </div>
                      
                      {/* Column 4: Time */}
                      <div className="text-[var(--text-muted)] font-mono text-sm">
                        {det.timestamp}
                      </div>
                      
                      {/* Column 5: Actions */}
                      <div className="text-right flex justify-end pr-2">
                        <button 
                          onClick={() => onDelete && onDelete(det.id)}
                          className="p-2 inline-flex items-center justify-center text-[var(--text-muted)] hover:text-[#ff5d73] hover:bg-[#ff5d73]/10 rounded-lg transition-all opacity-70 group-hover:opacity-100"
                          title="Delete detection"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
              </div>
            </div>
          )}
          
        </div>
        
      </div>
    </div>
  );
};

export default DetectionHistory;
