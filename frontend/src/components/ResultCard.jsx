import React, { useState } from 'react';
import { Plane, Hotel, Calendar, PiggyBank, Share2, Printer, ChevronRight } from 'lucide-react';

const ResultCard = ({ plan }) => {
  const [activeTab, setActiveTab] = useState('itinerary');

  if (!plan) return null;

  const {
    flight_results,
    hotel_results,
    itinerary,
    budget_analysis,
    budget,
    llm_calls,
    user_query
  } = plan;

  // Simple parser to render markdown/plain text text blocks beautifully
  const renderFormattedText = (text) => {
    if (!text) return <p className="text-brand-muted font-light italic">No data available.</p>;

    const lines = text.split('\n');
    return (
      <div className="space-y-5 text-left font-normal text-base sm:text-[17.5px] leading-relaxed text-slate-700">
        {lines.map((line, index) => {
          // Check for main headers (# Header or H1)
          if (line.startsWith('# ')) {
            return (
              <h3 key={index} className="text-3xl font-extrabold text-slate-800 mt-8 mb-4 pb-2 border-b border-brand-border">
                {line.substring(2)}
              </h3>
            );
          }
          // Check for H2 (## Header)
          if (line.startsWith('## ')) {
            return (
              <h4 key={index} className="text-2xl font-bold text-brand-accent mt-6 mb-3">
                {line.substring(3)}
              </h4>
            );
          }
          // Check for H3 (### Header)
          if (line.startsWith('### ')) {
            return (
              <h5 key={index} className="text-xl font-semibold text-slate-800 mt-5 mb-3">
                {line.substring(4)}
              </h5>
            );
          }
          // Check for bold points/day headings (e.g. **Day 1:** or similar)
          if (line.startsWith('- **') || line.startsWith('* **')) {
            const matches = line.match(/^[-*]\s+\*\*(.*?)\*\*(.*)/);
            if (matches) {
              return (
                <div key={index} className="flex gap-2.5 items-start pl-2">
                  <span className="text-brand-accent mt-2">•</span>
                  <p>
                    <strong className="text-slate-900 font-bold">{matches[1]}</strong>
                    {matches[2]}
                  </p>
                </div>
              );
            }
          }
          // Check for standard lists
          if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            return (
              <div key={index} className="flex gap-2.5 items-start pl-4">
                <span className="text-brand-accent mt-2">•</span>
                <p>{line.trim().substring(2)}</p>
              </div>
            );
          }
          // Check for standard numbered lists
          const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <div key={index} className="flex gap-3 items-start pl-2">
                <span className="text-brand-accent font-bold">{numMatch[1]}.</span>
                <p>{numMatch[2]}</p>
              </div>
            );
          }
          // Normal paragraph (ignore empty lines)
          if (line.trim() === '') return <div key={index} className="h-2"></div>;

          // Render line with bold inline text replacements
          const parts = [];
          let currentStr = line;
          const boldRegex = /\*\*(.*?)\*\*/g;
          let match;
          let lastIndex = 0;

          while ((match = boldRegex.exec(line)) !== null) {
            parts.push(line.substring(lastIndex, match.index));
            parts.push(<strong key={match.index} className="text-slate-900 font-bold">{match[1]}</strong>);
            lastIndex = boldRegex.lastIndex;
          }
          parts.push(line.substring(lastIndex));

          return <p key={index} className="text-slate-700">{parts.length > 1 ? parts : line}</p>;
        })}
      </div>
    );
  };

  // Helper to extract status from budget analysis
  const getBudgetBadge = (analysisText) => {
    if (!analysisText) return { label: 'Estimating', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30' };
    const textLower = analysisText.toLowerCase();
    
    if (textLower.includes('budget status: fits') || textLower.includes('status: fits') || textLower.includes('status: under')) {
      return { label: 'Under Budget', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    }
    if (textLower.includes('budget status: over') || textLower.includes('status: over')) {
      return { label: 'Over Budget', color: 'bg-red-50 text-red-700 border-red-200' };
    }
    return { label: 'Estimated Cost', color: 'bg-amber-50 text-amber-700 border-amber-200' };
  };

  const budgetBadge = getBudgetBadge(budget_analysis);

  const tabs = [
    { id: 'itinerary', label: 'Itinerary', icon: Calendar },
    { id: 'flights', label: 'Flights', icon: Plane },
    { id: 'hotels', label: 'Hotels', icon: Hotel },
    { id: 'budget', label: 'Budget Analysis', icon: PiggyBank },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-brand-border animate-fade-in text-slate-700">
      {/* Header Summary Panel */}
      <div className="p-6 sm:p-8 bg-gradient-to-b from-slate-50 to-white border-b border-brand-border flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-wider text-brand-accent font-semibold">Your Travel Plan</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-800 mt-1 capitalize leading-tight">
            {user_query.length > 60 ? `${user_query.slice(0, 60)}...` : user_query}
          </h2>
          <div className="flex flex-wrap items-center gap-4 mt-3">
            {budget > 0 && (
              <span className="text-xs sm:text-sm text-slate-500">
                Target Budget: <span className="text-slate-800 font-semibold">₹{budget.toLocaleString()}</span>
              </span>
            )}
            <span className={`text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded border ${budgetBadge.color}`}>
              {budgetBadge.label}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => window.print()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-slate-900 border border-brand-border text-sm font-medium transition-all duration-300 shadow-sm"
          >
            <Printer className="h-4 w-4" />
            Print
          </button>
          <div className="text-right text-xs text-slate-500 hidden sm:block">
            <span className="block text-slate-800 font-semibold">{llm_calls} Agent Calls</span>
            System optimized
          </div>
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-slate-200 bg-slate-50 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 px-6 py-4 text-sm font-semibold border-b-2 whitespace-nowrap transition-all duration-300
                ${isActive 
                  ? 'border-brand-accent text-brand-accent bg-white' 
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
                }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="p-6 sm:p-8 min-h-[300px] bg-white">
        {activeTab === 'itinerary' && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-5 w-5 text-brand-accent" />
              <h3 className="text-lg font-bold text-slate-800">Suggested Day-by-Day Route</h3>
            </div>
            {renderFormattedText(itinerary)}
          </div>
        )}

        {activeTab === 'flights' && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <Plane className="h-5 w-5 text-brand-accent" />
              <h3 className="text-lg font-bold text-slate-800">Recommended Flight Routes</h3>
            </div>
            {renderFormattedText(flight_results)}
          </div>
        )}

        {activeTab === 'hotels' && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <Hotel className="h-5 w-5 text-brand-accent" />
              <h3 className="text-lg font-bold text-slate-800">Top Accommodation Stays</h3>
            </div>
            {renderFormattedText(hotel_results)}
          </div>
        )}

        {activeTab === 'budget' && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <PiggyBank className="h-5 w-5 text-brand-accent" />
              <h3 className="text-lg font-bold text-slate-800">Budget Evaluation & Advice</h3>
            </div>
            {renderFormattedText(budget_analysis)}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultCard;
