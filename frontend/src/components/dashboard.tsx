import { createSignal, Show, onMount } from 'solid-js';
import type { Component } from 'solid-js';
import { Alerts } from './alerts';
import { PulseChart } from './pulse-chart';
import { ChatSidebar } from './chat-sidebar';

export const Dashboard: Component = () => {
  const [criticalAlerts, setCriticalAlerts] = createSignal<{message: string, action_type: string}[]>([]);
  const [chartMode, setChartMode] = createSignal<'sales' | 'inventory'>('sales');
  const [dynamicChartData, setDynamicChartData] = createSignal<any>(null);
  const [isChartVisible, setIsChartVisible] = createSignal(false);
  const [isVisualExpanded, setIsVisualExpanded] = createSignal(false);
  const [isLoading, setIsLoading] = createSignal(true);

  onMount(async () => {
    try {
      const res = await fetch(`/api/get-sales-prediction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'initial load' })
      });
      const data = await res.json();
      if (data.action_type && data.action_type !== 'none') {
        handleActionTypeReceived(data.action_type, data.alert_data);
      }
    } catch (err) {
      console.error("Failed to load initial chart data:", err);
    } finally {
      setIsLoading(false);
    }
  });

  const handleActionTypeReceived = (action_type: string, payload?: any) => {
    // For the new /ask-nk-ai endpoint, chart fields are directly on payload (not nested under chart_data)
    const chartPayload = payload?.labels || payload?.type || payload?.pie_labels ? payload : payload?.chart_data;
    
    if (action_type === 'legal_notice') {
      const amt = payload?.top_defaulter_amount?.toLocaleString() || payload?.top_debt_amount?.toLocaleString() || '70,00,000';
      const maxDays = payload?.max_days || 60;
      const cust = payload?.top_defaulter || payload?.top_debtor || 'Customer';
      setCriticalAlerts(prev => {
        const filtered = prev.filter(a => a.action_type !== 'legal_notice');
        return [...filtered, {
          message: `₹${amt} stuck with ${cust}, >${maxDays} days overdue.`,
          action_type: "legal_notice"
        }];
      });
      setChartMode('sales');
      if (chartPayload) setDynamicChartData(chartPayload);
    } else if (action_type === 'liquidate_stock') {
      const prod = payload?.dead_product || 'De Oiled Cake';
      const days = payload?.days_stuck || 120;
      setCriticalAlerts(prev => {
        const filtered = prev.filter(a => a.action_type !== 'liquidate_stock');
        return [...filtered, {
          message: `${prod} Dead Stock (${days} days). Focus: Liquidation.`,
          action_type: "liquidate_stock"
        }];
      });
      setChartMode('inventory');
      if (chartPayload) setDynamicChartData(chartPayload);
    } else if (action_type === 'reconcile_tax') {
      const mismatch = payload?.mismatch?.toLocaleString() || '15,00,000';
      setCriticalAlerts(prev => {
        const filtered = prev.filter(a => a.action_type !== 'reconcile_tax');
        return [...filtered, {
          message: `₹${mismatch} mismatch in recent GSTR-2B log.`,
          action_type: "reconcile_tax"
        }];
      });
      setChartMode('sales');
      if (chartPayload) setDynamicChartData(chartPayload);
    } else if (action_type === 'sales_view') {
      setChartMode('sales');
      if (chartPayload) setDynamicChartData(chartPayload);
    }
  };

  return (
    <div class="flex-1 w-full h-full overflow-hidden bg-slate-950 text-slate-100 flex flex-col p-4 md:p-6 gap-4 md:gap-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black font-sans">
      
      {/* Universal Header */}
      <header class="bg-white/5 backdrop-blur-xl border border-white/10 p-2 md:p-4 rounded-3xl shadow-2xl flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-xl md:text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
            NK Proteins CMD Co-pilot
          </h1>
          <p class="text-slate-400 mt-1 text-xs md:text-sm font-medium tracking-wide">AI-Driven Executive Intelligence</p>
        </div>
        <div class="flex items-center gap-4">
           <button 
              onClick={() => setIsChartVisible(!isChartVisible())}
              class="hidden lg:block text-xs bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-200 px-4 py-2 rounded-xl transition font-bold border border-indigo-500/30 shadow-lg shadow-indigo-500/20"
           >
              {isChartVisible() ? 'Close Visuals ▲' : 'Open Visuals ▼'}
           </button>
           <div class="hidden md:flex items-center gap-3">
             <div class="h-3 w-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.7)]"></div>
             <span class="text-sm font-semibold text-slate-300">NK AI Live</span>
           </div>
        </div>
      </header>

      {/* Full-Screen Expanded Visual Modal */}
      <Show when={isVisualExpanded()}>
        <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10 pointer-events-auto">
          <div 
            class="absolute inset-0 bg-slate-950/80 backdrop-blur-2xl transition-opacity animate-in fade-in duration-300" 
            onClick={() => setIsVisualExpanded(false)}
          ></div>
          
          <div class="relative w-full h-full max-w-7xl bg-white/5 border border-white/10 rounded-[2rem] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
             <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 pointer-events-none"></div>
             
             <div class="px-8 py-6 border-b border-white/10 flex items-center justify-between relative z-10">
                <div class="flex items-center gap-4">
                   <div class="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                      </svg>
                   </div>
                   <div>
                      <h2 class="text-2xl font-bold text-slate-100 tracking-tight">Expanded Intelligence View</h2>
                      <p class="text-slate-400 text-sm font-medium">Real-time data synchronization active</p>
                   </div>
                </div>
                
                <button 
                  onClick={() => setIsVisualExpanded(false)}
                  class="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                   </svg>
                </button>
             </div>
             
             <div class="flex-1 p-8 relative z-10 overflow-hidden">
                <Show when={!isLoading()} fallback={
                  <div class="flex flex-col items-center justify-center h-full">
                     <div class="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                  </div>
                }>
                  <div class="h-full w-full">
                    <PulseChart mode={chartMode()} dynamicData={dynamicChartData()} />
                  </div>
                </Show>
             </div>
          </div>
        </div>
      </Show>

      {/* Main Body Grid */}
      <div class="flex flex-col lg:flex-row flex-1 gap-4 md:gap-6 min-h-0">
        
        {/* Left Visuals Container */}
        <Show when={isChartVisible()}>
          <div class="flex flex-col w-full lg:w-2/3 xl:w-3/4 gap-4 md:gap-6 overflow-y-auto h-full pr-0 lg:pr-2 pb-4">
            
            {/* Alerts Grid */}
            <Alerts
              alerts={criticalAlerts()}
              onDismiss={(action_type) => setCriticalAlerts(prev => prev.filter(a => a.action_type !== action_type))}
            />

            {/* Dynamic Data Visualization Area */}
            <div class="flex-1 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl p-4 md:p-6 flex flex-col group relative overflow-hidden transition-all duration-300 min-h-[400px]">
              <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
              
              <div class="flex justify-between items-center mb-4 md:mb-6">
                <h2 class="text-lg md:text-xl font-bold text-slate-200 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 md:h-6 md:w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                  Live Metrix Pulse
                </h2>
                <button 
                  onClick={() => setIsVisualExpanded(true)}
                  class="text-xs bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 px-3 py-1.5 rounded-xl border border-indigo-500/30 transition flex items-center gap-2 shadow-lg shadow-indigo-500/10"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                  Expand View
                </button>
              </div>
              
              <div class="flex-1 relative overflow-x-auto">
                 <Show when={!isLoading()} fallback={
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                       <div class="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                       <p class="mt-4 text-slate-400 font-medium animate-pulse">Synchronizing Core Engine...</p>
                    </div>
                 }>
                    <div class="min-w-[600px] h-full">
                      <PulseChart mode={chartMode()} dynamicData={dynamicChartData()} />
                    </div>
                 </Show>
              </div>
            </div>
          </div>
        </Show>

        {/* Sidebar Chat */}
        <div class={`flex flex-col h-full overflow-hidden transition-all duration-500 ${isChartVisible() ? 'w-full lg:w-1/2 xl:w-1/2 pt-2 lg:pt-0' : 'w-full'}`}>
          <ChatSidebar onActionReceived={handleActionTypeReceived} />
        </div>

      </div>
    </div>
  );
};
