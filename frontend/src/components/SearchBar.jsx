import React, { useState } from 'react';
import { Search, Compass, AlertCircle } from 'lucide-react';

const SearchBar = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  const suggestions = [
    { text: "Plan 3 days trip to Shimla under 15,000 INR", label: "Shimla (Budget)" },
    { text: "5 days luxury vacation to Goa", label: "Goa (Luxury)" },
    { text: "Delhi to Manali weekend getaway under 8000", label: "Manali weekend" },
    { text: "Explore Udaipur culture for 4 days", label: "Udaipur cultural" }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please describe your travel plans first');
      return;
    }
    setError('');
    onSearch(query);
  };

  return (
    <div className="w-full max-w-3xl mx-auto mb-10 text-center">
      <h1 className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-700 mb-4 tracking-tight">
        Plan Your Next Adventure
      </h1>
      <p className="text-brand-muted text-base sm:text-lg mb-8 max-w-xl mx-auto font-light">
        Our multi-agent AI system will search flights, hotels, plan itineraries, and optimize your budget.
      </p>

      <form onSubmit={handleSubmit} className="relative group mb-6">
        <div className="absolute -inset-1.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl blur opacity-15 group-hover:opacity-25 transition duration-1000 group-focus-within:opacity-30"></div>
        <div className="relative flex items-center bg-brand-card border border-brand-border rounded-xl p-2.5 shadow-xl">
          <Compass className="h-6 w-6 text-brand-muted ml-3 animate-pulse-slow" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            placeholder="Where do you want to go? (e.g., Delhi to Manali for 3 days under ₹15000)"
            className="w-full bg-transparent border-0 outline-none text-slate-800 placeholder-slate-400 px-4 text-sm sm:text-base font-light focus:ring-0 focus:outline-none"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="flex items-center gap-2 px-6 py-2.5 sm:py-3 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-brand-border disabled:to-brand-border disabled:text-brand-muted text-white font-medium text-sm rounded-lg transition-all duration-300 shadow-lg"
          >
            {isLoading ? 'Planning...' : 'Generate Plan'}
            {!isLoading && <Search className="h-4 w-4" />}
          </button>
        </div>
      </form>

      {error && (
        <div className="flex items-center justify-center gap-2 text-red-400 text-sm mb-4 animate-shake">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Suggested Chips */}
      <div className="flex flex-wrap justify-center items-center gap-2 mt-4">
        <span className="text-xs text-brand-muted mr-1">Suggestions:</span>
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setQuery(suggestion.text)}
            disabled={isLoading}
            className="text-xs px-3.5 py-1.5 rounded-full bg-white hover:bg-slate-50 border border-brand-border text-slate-600 hover:text-slate-800 transition-all duration-300 font-medium shadow-sm"
          >
            {suggestion.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SearchBar;
