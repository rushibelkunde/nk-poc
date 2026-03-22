import { createSignal, createEffect, For, Show } from 'solid-js';
import type { Component } from 'solid-js';
import { marked } from 'marked';

type Message = {
  id: string;
  role: 'user' | 'ai';
  content: string;
};

export const ChatSidebar: Component<{ onActionReceived: (type: string, payload?: any) => void }> = (props) => {
  const [messages, setMessages] = createSignal<Message[]>([
    { id: '1', role: 'ai', content: 'Welcome to the Executive Command Center. How can I assist you today?' }
  ]);
  const [input, setInput] = createSignal('');
  const [isLoading, setIsLoading] = createSignal(false);
  let chatContainerRef: HTMLDivElement | undefined;


  createEffect(() => {
    messages(); // track array changes
    if (chatContainerRef) chatContainerRef.scrollTop = chatContainerRef.scrollHeight;
  });

  const handleQuerySelect = (query: string) => {
    if (query === "") return;
    setInput(query);
    sendMessage();
  };

  const sendMessage = async () => {
    if (!input().trim() || isLoading()) return;

    const userMsg = input().trim();
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: userMsg }]);
    setInput('');
    setIsLoading(true);

    const endpoint = '/ask-nk-ai';

    try {
      const res = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg })
      });
      
      const data = await res.json();
      
      if (data.action_type && data.action_type !== 'none') {
        props.onActionReceived(data.action_type, data.alert_data);
      }
      
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', content: data.response }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', content: 'Error: Cannot reach NK AI Engine Node. Ensure backend is running.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div class="flex flex-col h-full bg-transparent overflow-hidden">
      <div class="px-6 py-3 border-b border-nkBorder flex items-center justify-between shadow-sm">
        <div class="flex flex-col">
          <h2 class="text-lg font-black text-nkText">CoPilot Interaction</h2>
          <p class="text-[9px] text-slate-500 font-bold uppercase tracking-wider opacity-60">AI-Powered Executive Intelligence</p>
        </div>
        <button 
          onClick={() => setMessages([{ id: Date.now().toString(), role: 'ai', content: 'Conversation cleared. How can I assist you today?' }])}
          class="text-[9px] text-slate-500 hover:text-nkAccent transition-colors uppercase font-black tracking-widest flex items-center gap-1 p-1.5 hover:bg-white/5 rounded-lg border border-transparent hover:border-nkBorder"
          title="Clear History"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Reset
        </button>
      </div>
      
      <div ref={chatContainerRef} class="flex-1 overflow-y-auto p-4 md:p-6 flex flex-col gap-6 min-h-0 scroll-smooth">
        {/* Executive Guidance Tools (Quick Actions Grid) */}
        <div class="mb-1">
          <h3 class="text-[10px] font-black text-nkHighlight uppercase tracking-[0.2em] mb-3 ml-1">Executive Guidance Tools</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {[
              "Predict next quarter sales with exact numbers",
              "Who are my top 5 slow paying customers?",
              "Which products should I discontinue and why?",
              "Generate a full executive report",
              "What is my cash flow risk this month?",
              "Show me all GST mismatches and ITC at risk",
              "Which dead stock items should I liquidate first?",
              "Which customers are in the low margin risk segment?"
            ].map((q) => (
              <button 
                onClick={() => handleQuerySelect(q)}
                class="text-left text-[10px] bg-white/5 hover:bg-white/10 border border-nkBorder text-slate-400 hover:text-white p-2 rounded-lg transition-all duration-200 font-bold shadow-sm active:scale-95 leading-tight min-h-[40px]"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <For each={messages()}>
            {(msg) => (
              <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div class={`max-w-[90%] rounded-[1.5rem] p-5 md:p-6 ${msg.role === 'user' ? 'bg-white/5 border border-white/10 text-white rounded-br-none' : 'bg-black/20 text-slate-200 border border-white/5 shadow-xl rounded-bl-none'}`}>
                  <div class="flex items-center gap-2 mb-3 opacity-40 text-[9px] uppercase font-black tracking-[0.2em] text-slate-400">
                    {msg.role === 'user' ? 'Executive' : 'NK CoPilot'}
                  </div>
                  <div 
                    class={`text-sm leading-relaxed 
                           [&_p]:mb-4 [&_p:last-child]:mb-0
                           [&_strong]:text-white [&_strong]:font-black
                           [&_h3]:text-base [&_h3]:font-black [&_h3]:text-white [&_h3]:mb-4 [&_h3]:mt-6 [&_h3]:uppercase
                           [&_table]:w-full [&_table]:my-6 [&_table]:border-collapse [&_table]:text-[11px] [&_table]:rounded-xl [&_table]:overflow-hidden
                           [&_th]:p-3 [&_th]:border-b [&_th]:border-white/10 [&_th]:bg-white/5 [&_th]:text-white [&_th]:font-black [&_th]:uppercase
                           [&_td]:p-3 [&_td]:border-b [&_td]:border-white/5 [&_td]:text-slate-400`}
                    innerHTML={marked.parse(msg.content) as string} 
                  />
                </div>
              </div>
            )}
          </For>
        </div>
        
        <Show when={isLoading()}>
          <div class="flex justify-start">
            <div class="bg-black/20 rounded-2xl p-4 w-20 flex justify-center items-center gap-1.5 border border-white/5">
              <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"></div>
              <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.5s]"></div>
            </div>
          </div>
        </Show>
      </div>

      <div class="p-6 md:p-8 border-t border-nkBorder relative overflow-hidden group">
        
        <div class="max-w-5xl mx-auto flex flex-col sm:flex-row gap-4 relative">
          <select 
            onChange={(e) => handleQuerySelect(e.currentTarget.value)}
            class="bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-xs text-slate-300 focus:outline-none focus:border-white/20 font-bold max-w-full sm:max-w-[250px]"
          >
            <option value="" class="bg-nkPrimary">Quick Intelligence Tools...</option>
            {[
              "Give me a summary of current business performance",
              "How have our sales trended from 2022 till now?",
              "Predict next quarter sales",
              "Show top profitable products",
              "Which customers are low margin despite high sales?",
              "Which products should we promote next month?",
              "Which customers are slow-paying?",
              "How much cash do we need in next 30 days?",
              "Which items are dead stock?",
              "How much capital is blocked in inventory?",
              "Show GST mismatch summary",
              "What should I focus on in next 30 days?",
              "What are the top risks in the business right now?",
              "What is blocking my working capital?"
            ].map(q => <option value={q} class="bg-nkPrimary text-nkText">{q}</option>)}
          </select>

          <input 
            type="text" 
            value={input()}
            onInput={(e) => setInput(e.currentTarget.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask your CoPilot anything about NK Protein's data..."
            class="flex-1 bg-white/5 border border-white/10 rounded-2xl px-6 py-5 text-sm focus:outline-none focus:border-white/20 text-nkText placeholder-slate-600 transition-all font-bold"
            disabled={isLoading()}
          />
          <button 
            onClick={sendMessage}
            class="bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-2xl px-6 py-5 transition-all disabled:opacity-30 active:scale-95 flex items-center justify-center shrink-0"
            disabled={isLoading() || !input().trim()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>
        <p class="text-[9px] text-center mt-4 text-slate-600 font-bold uppercase tracking-widest opacity-60">Press Enter to send • Verified SAP Intelligent Insights</p>
      </div>
    </div>
  );
};
