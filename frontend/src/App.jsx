import React, { useState, useEffect } from 'react';
import { Compass, Menu, X, AlertTriangle, History } from 'lucide-react';
import axios from 'axios';

// Components
import SearchBar from './components/SearchBar';
import LoadingState from './components/LoadingState';
import ResultCard from './components/ResultCard';
import TripHistory from './components/TripHistory';

const BACKEND_URL = 'http://localhost:8000';

function App() {
  const [threadId, setThreadId] = useState(null);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [plan, setPlan] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Fetch travel plans history
  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/history`);
      if (response.data && response.data.history) {
        setHistory(response.data.history);
      }
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Handle new search query (streaming response)
  const handleSearch = async (query) => {
    setIsLoading(true);
    setIsStreaming(true);
    setError('');
    setCurrentAgent('flight_agent'); // start state
    setPlan({
      user_query: query,
      flight_results: '',
      hotel_results: '',
      itinerary: '',
      budget_analysis: '',
      budget: 0,
      llm_calls: 0
    });

    const activeThreadId = threadId || null;

    try {
      const response = await fetch(`${BACKEND_URL}/api/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_query: query,
          thread_id: activeThreadId
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;

          const lines = part.split('\n');
          let eventType = '';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.substring(7).trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.substring(6).trim();
            }
          }

          if (dataStr) {
            const data = JSON.parse(dataStr);
            if (eventType === 'start') {
              setThreadId(data.thread_id);
              setPlan(prev => ({ ...prev, budget: data.budget }));
            } else if (eventType === 'update') {
              const { agent, output } = data;
              setCurrentAgent(agent);
              setPlan((prev) => {
                const updated = { ...prev };
                if (output.flight_results) updated.flight_results = output.flight_results;
                if (output.hotel_results) updated.hotel_results = output.hotel_results;
                if (output.itinerary) updated.itinerary = output.itinerary;
                if (output.budget_analysis) updated.budget_analysis = output.budget_analysis;
                if (output.llm_calls !== undefined) updated.llm_calls = output.llm_calls;
                return updated;
              });
            } else if (eventType === 'complete') {
              setIsLoading(false);
              setIsStreaming(false);
              fetchHistory();
            } else if (eventType === 'error') {
              setError(data.message);
              setIsLoading(false);
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'An unexpected connection error occurred.');
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  // Select a past plan from history sidebar
  const handleSelectThread = async (id) => {
    setIsLoading(true);
    setIsStreaming(false);
    setError('');
    setSidebarOpen(false); // Close sidebar on mobile
    
    try {
      const response = await axios.get(`${BACKEND_URL}/api/plan/${id}`);
      if (response.data && !response.data.error) {
        setThreadId(response.data.thread_id);
        setPlan(response.data);
      } else {
        setError(response.data.error || 'Failed to fetch plan.');
      }
    } catch (err) {
      console.error("Failed to select plan:", err);
      setError('Connection to backend failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // Start fresh plan session
  const handleNewTrip = () => {
    setThreadId(null);
    setPlan(null);
    setCurrentAgent(null);
    setError('');
    setIsLoading(false);
    setIsStreaming(false);
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden text-slate-800 font-sans">
      
      {/* Floating Sidebar Toggle Button */}
      <button 
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-6 left-6 z-50 p-2.5 rounded-xl bg-white/90 backdrop-blur-md border border-brand-border text-slate-700 hover:text-slate-900 hover:bg-slate-100 hover:border-brand-accent/50 shadow-lg transition-all duration-300 group cursor-pointer"
        title="Toggle History"
      >
        {sidebarOpen ? (
          <X className="h-5 w-5 text-brand-accent animate-pulse-slow" />
        ) : (
          <History className="h-5 w-5 text-brand-accent group-hover:rotate-[-12deg] transition-transform duration-200" />
        )}
      </button>

      {/* Sidebar - Trip History */}
      <div className={`fixed inset-y-0 left-0 z-40 w-72 transform transition-transform duration-300 ease-in-out border-r border-brand-border bg-slate-50/95 backdrop-blur-md shadow-2xl
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <TripHistory 
          history={history}
          activeThreadId={threadId}
          onSelectThread={handleSelectThread}
          onNewTrip={handleNewTrip}
        />
      </div>

      {/* Background Overlay for sidebar */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-slate-950/20 backdrop-blur-[2px] transition-all duration-300"
        ></div>
      )}

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col overflow-y-auto px-4 py-8 sm:p-8 md:p-12 relative min-h-screen">
        
        {/* Header Branding */}
        <div className="flex items-center gap-2 mb-10 max-w-4xl mx-auto w-full pl-12 sm:pl-14 md:pl-0">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <Compass className="h-5 w-5" />
          </div>
          <span className="font-extrabold tracking-wide text-lg bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-800">
            AEROSPLAN
          </span>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="max-w-4xl mx-auto w-full mb-6 p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <h5 className="font-semibold text-sm">System Error</h5>
              <p className="text-xs text-red-600 mt-1 font-light">{error}</p>
            </div>
          </div>
        )}

        {/* Dynamic Display Layout */}
        <div className="flex-1 flex flex-col justify-center items-center max-w-4xl mx-auto w-full">
          
          {!plan && !isLoading && (
            <div className="my-auto py-10 w-full">
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </div>
          )}

          {isLoading && isStreaming && (
            <div className="my-auto py-10 w-full">
              <LoadingState currentAgent={currentAgent} isStreaming={isStreaming} />
            </div>
          )}

          {plan && (!isLoading || !isStreaming) && (
            <div className="w-full space-y-8 pb-10">
              <ResultCard plan={plan} />
              
              {/* Floating action bar to plan again */}
              <div className="flex justify-center mt-6">
                <button
                  onClick={handleNewTrip}
                  className="px-6 py-2.5 rounded-lg bg-white hover:bg-slate-100 text-brand-muted hover:text-slate-800 border border-brand-border text-sm font-medium transition-all duration-300 shadow-sm"
                >
                  Plan Another Journey
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
