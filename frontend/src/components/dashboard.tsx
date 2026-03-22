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
    <div class="flex-1 w-full h-full overflow-hidden bg-nkPrimary text-nkText flex flex-col p-4 md:p-5 gap-4 font-sans">
      
      {/* Universal Header - Re-styled for NK Proteins Branding */}
      <header class="bg-nkPrimary border-b border-nkBorder pb-4 flex flex-col md:flex-row md:items-end justify-between shrink-0 gap-4">
        <div>
          <h1 class="text-2xl md:text-3xl font-black tracking-tight text-nkText">
            NK Proteins CMD CoPilot
          </h1>
          <div class="flex items-center gap-3 mt-1">
            <span class="px-2 py-0.5 bg-nkAccent text-white text-[9px] font-black rounded uppercase tracking-wider">Executive v1.2</span>
            <p class="text-slate-500 text-[10px] md:text-xs font-semibold tracking-wide opacity-70">Real-time SAP Intelligent Intelligence Engine</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
           <button 
              onClick={() => setIsChartVisible(!isChartVisible())}
              class="text-[10px] bg-nkCard hover:bg-slate-700 text-white px-4 py-2 rounded-xl transition font-bold shadow-md border border-nkBorder active:scale-95"
           >
              {isChartVisible() ? 'Hide Visuals' : 'Show Visuals'}
           </button>
           <div class="hidden md:flex items-center gap-3 bg-nkCard px-3 py-1.5 rounded-xl border border-nkBorder">
             <div class="h-1.5 w-1.5 bg-green-500 rounded-full animate-pulse"></div>
             <span class="text-[10px] font-bold text-slate-400 tracking-wider">NK AI Engine Linked</span>
           </div>
        </div>
      </header>

      {/* Main Body Grid */}
      <div class="flex flex-col lg:flex-row flex-1 gap-6 min-h-0 overflow-hidden">
        
        {/* Visuals Container (Dashboard) */}
        <Show when={isChartVisible()}>
          <div class="flex flex-col w-full lg:w-3/5 gap-6 overflow-y-auto h-full pr-2 pb-4">
            
            {/* Alerts Grid */}
            <Alerts
              alerts={criticalAlerts()}
              onDismiss={(action_type) => setCriticalAlerts(prev => prev.filter(a => a.action_type !== action_type))}
            />

            {/* Dynamic Data Visualization Area */}
            <div class="flex-1 bg-nkCard border border-nkBorder rounded-[2rem] shadow-sm p-6 flex flex-col min-h-[500px] transition-all">
              <div class="flex justify-between items-center mb-8">
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-white/5 rounded-xl text-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                  </div>
                  <div>
                    <h2 class="text-xl font-black text-nkText tracking-tight">Analytics Deep-Dive</h2>
                    <p class="text-[11px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Live Data Visualisation</p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsVisualExpanded(true)}
                  class="text-[11px] bg-white/5 hover:bg-white/10 text-slate-300 px-4 py-2 rounded-xl border border-nkBorder font-black uppercase tracking-wider transition active:scale-95"
                >
                  Expand Insights
                </button>
              </div>
              
              <div class="flex-1 relative overflow-hidden bg-black/20 rounded-2xl border border-nkBorder">
                 <Show when={!isLoading()} fallback={
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                       <div class="w-10 h-10 border-4 border-white/10 border-t-nkAccent rounded-full animate-spin"></div>
                       <p class="mt-4 text-slate-500 text-xs font-bold uppercase tracking-widest animate-pulse">Running Calculations...</p>
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

        {/* Sidebar Chat (Now takes main focus if visuals closed) */}
        <div class={`flex flex-col h-full overflow-hidden transition-all duration-500 ${isChartVisible() ? 'w-full lg:w-2/5' : 'w-full max-w-5xl mx-auto'}`}>
          <ChatSidebar onActionReceived={handleActionTypeReceived} />
        </div>

      </div>

      {/* Expanded Intelligence View Overlay */}
      <Show when={isVisualExpanded()}>
        <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8">
          <div class="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={() => setIsVisualExpanded(false)}></div>
          <div class="relative w-full h-full max-w-7xl bg-nkCard rounded-[3rem] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 border border-nkBorder">
             <div class="px-8 py-6 border-b border-nkBorder flex items-center justify-between">
                <div class="flex items-center gap-4">
                   <div class="p-3 bg-nkAccent rounded-2xl text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                      </svg>
                   </div>
                   <div>
                      <h2 class="text-2xl font-black text-nkText tracking-tight">Predictive Insight Engine</h2>
                      <p class="text-slate-400 text-xs font-bold tracking-widest mt-1 uppercase">Full-Scale Intelligence Visualisation</p>
                   </div>
                </div>
                <button onClick={() => setIsVisualExpanded(false)} class="p-3 bg-white/5 hover:bg-white/10 rounded-full transition-colors text-slate-400 active:scale-95">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
             </div>
             <div class="flex-1 p-8 overflow-hidden bg-black/20">
                <Show when={!isLoading()}>
                   <PulseChart mode={chartMode()} dynamicData={dynamicChartData()} />
                </Show>
             </div>
          </div>
        </div>
      </Show>
    </div>
  );
};
