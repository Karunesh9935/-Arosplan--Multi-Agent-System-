import React from 'react';
import { Plane, Hotel, Map, PiggyBank, FileText, CheckCircle2, Loader2 } from 'lucide-react';

const LoadingState = ({ currentAgent, isStreaming }) => {
  const steps = [
    {
      id: 'flight_agent',
      name: 'Flight Search Agent',
      description: 'Finding flight schedules, airlines, and routes...',
      icon: Plane,
      color: 'from-blue-500 to-indigo-600',
    },
    {
      id: 'hotel_agent',
      name: 'Hotel Selection Agent',
      description: 'Searching accommodations and hotels via Tavily...',
      icon: Hotel,
      color: 'from-teal-500 to-emerald-600',
    },
    {
      id: 'itinerary_agent',
      name: 'Itinerary Planner Agent',
      description: 'Drafting day-by-day activities and food ideas...',
      icon: Map,
      color: 'from-purple-500 to-pink-600',
    },
    {
      id: 'budget_agent',
      name: 'Budget Analysis Agent',
      description: 'Calculating costs and comparing with target budget...',
      icon: PiggyBank,
      color: 'from-amber-500 to-orange-600',
    },
    {
      id: 'final_agent',
      name: 'Final Plan Architect',
      description: 'Assembling and polishing your final travel guide...',
      icon: FileText,
      color: 'from-indigo-500 to-purple-600',
    },
  ];

  // Helper to determine status of a step
  const getStepStatus = (stepId, index) => {
    if (!isStreaming) return 'waiting';
    if (currentAgent === stepId) return 'running';
    
    // Find index of current running agent
    const currentAgentIndex = steps.findIndex(s => s.id === currentAgent);
    
    if (currentAgentIndex === -1) {
      // If we haven't started or are done, check context
      return 'waiting';
    }
    
    if (index < currentAgentIndex) return 'completed';
    return 'waiting';
  };

  return (
    <div className="bg-white rounded-2xl p-8 max-w-2xl mx-auto shadow-xl border border-brand-border animate-fade-in">
      <div className="flex items-center gap-4 mb-8 pb-4 border-b border-brand-border">
        <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center text-brand-accent">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-slate-800">AI Agents Planning Your Trip</h3>
          <p className="text-sm text-brand-muted font-medium">Multi-agent system coordinating in real-time</p>
        </div>
      </div>

      <div className="relative border-l border-brand-border ml-6 pl-8 space-y-8">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id, index);
          const Icon = step.icon;

          return (
            <div key={step.id} className="relative transition-all duration-300">
              {/* Dot / Icon on the vertical line */}
              <div className={`absolute -left-[45px] top-1.5 h-8 w-8 rounded-full border-2 flex items-center justify-center transition-all duration-500
                ${status === 'completed' 
                  ? 'bg-emerald-50 border-brand-success text-brand-success' 
                  : status === 'running'
                  ? 'bg-indigo-50 border-brand-accent text-brand-accent shadow-[0_0_15px_rgba(79,70,229,0.35)] animate-pulse'
                  : 'bg-slate-50 border-brand-border text-brand-muted'
                }`}
              >
                {status === 'completed' ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : status === 'running' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>

              {/* Step Info */}
              <div className={`transition-all duration-300 ${status === 'running' ? 'scale-[1.02]' : 'opacity-70'}`}>
                <div className="flex items-center gap-2">
                  <h4 className={`font-semibold ${status === 'running' ? 'text-brand-accent font-bold' : status === 'completed' ? 'text-brand-success font-semibold' : 'text-slate-700 font-medium'}`}>
                    {step.name}
                  </h4>
                  {status === 'running' && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-accent/10 text-brand-accent font-medium uppercase tracking-wider animate-pulse">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-sm text-brand-muted mt-1 font-light">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LoadingState;
