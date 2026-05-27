import React from 'react';
import { History, Compass, ArrowRight, PlusCircle, Brain } from 'lucide-react';

const TripHistory = ({ history, activeThreadId, onSelectThread, onNewTrip }) => {
  return (
    <div className="w-full flex flex-col h-full bg-brand-dark/40 border-r border-brand-border text-left">
      {/* Header */}
      <div className="p-4 border-b border-brand-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-brand-accent" />
          <h2 className="text-lg font-bold text-slate-800 tracking-tight">Trip History</h2>
        </div>
        <button
          onClick={onNewTrip}
          className="p-1.5 rounded-lg hover:bg-brand-border text-brand-muted hover:text-slate-800 transition-all duration-300 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider cursor-pointer"
          title="Start New Plan"
        >
          <PlusCircle className="h-4.5 w-4.5 text-brand-accent" />
          New
        </button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center p-6 mt-10">
            <Compass className="h-10 w-10 text-brand-muted/40 mb-3 animate-bounce" />
            <p className="text-sm text-brand-muted font-light">No saved itineraries found.</p>
            <p className="text-xs text-brand-muted/70 mt-1 font-light">Your plans will save automatically.</p>
          </div>
        ) : (
          history.map((item) => {
            const isActive = item.thread_id === activeThreadId;
            return (
              <button
                key={item.thread_id}
                onClick={() => onSelectThread(item.thread_id)}
                className={`w-full p-3.5 rounded-xl border text-left transition-all duration-300 flex flex-col gap-2 group cursor-pointer
                  ${isActive 
                    ? 'bg-brand-accent/10 border-brand-accent text-brand-accent font-semibold shadow-md' 
                    : 'bg-white border-brand-border/60 hover:border-brand-border text-slate-650 hover:text-slate-800 shadow-sm'
                  }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold line-clamp-2 capitalize break-words pr-2">
                    {item.user_query}
                  </span>
                  <ArrowRight className={`h-3.5 w-3.5 mt-0.5 text-brand-muted transition-transform duration-300 group-hover:translate-x-0.5
                    ${isActive ? 'text-brand-accent opacity-100' : 'opacity-0 group-hover:opacity-100'}`} 
                  />
                </div>

                <div className="flex items-center justify-between text-[10px] text-brand-muted mt-1 border-t border-brand-border/30 pt-2">
                  <div className="flex items-center gap-1">
                    <Brain className="h-3 w-3 text-brand-accent/70" />
                    <span>{item.llm_calls} Agent Calls</span>
                  </div>
                  {item.budget > 0 && (
                    <span className="font-semibold text-slate-700 bg-brand-border/60 px-1.5 py-0.5 rounded">
                      ₹{item.budget.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};

export default TripHistory;
