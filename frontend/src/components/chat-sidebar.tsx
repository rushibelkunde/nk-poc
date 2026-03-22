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
    <div class="flex flex-col h-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
      <div class="px-6 py-5 bg-black/20 border-b border-white/10 flex items-center justify-between">
        <h2 class="text-lg font-bold text-slate-200">Executive AI Chat</h2>
        <div class="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30">AI Ready</div>
      </div>
      
      <div ref={chatContainerRef} class="flex-1 overflow-y-auto p-6 flex flex-col gap-4 min-h-0 scroll-smooth">
        <For each={messages()}>
          {(msg) => (
            <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div class={`max-w-[85%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-indigo-600 shadow-[0_0_15px_rgba(79,70,229,0.3)] text-white rounded-br-none' : 'bg-slate-800/80 text-slate-200 border border-slate-700 shadow-xl rounded-bl-none'}`}>
                <div 
                  class={`text-sm leading-relaxed 
                         [&_p]:mb-2 [&_p:last-child]:mb-0
                         [&_strong]:text-indigo-300 [&_strong]:font-bold
                         [&_h3]:text-base md:[&_h3]:text-lg [&_h3]:font-bold [&_h3]:text-indigo-400 [&_h3]:mb-2 [&_h3]:mt-3
                         [&_table]:w-full [&_table]:my-3 [&_table]:border-collapse [&_table]:text-left [&_table]:text-xs md:[&_table]:text-sm
                         [&_th]:p-2 [&_th]:border-b [&_th]:border-slate-600 [&_th]:bg-slate-700/50 [&_th]:text-indigo-200
                         [&_td]:p-2 [&_td]:border-b [&_td]:border-slate-700/50`}
                  innerHTML={marked.parse(msg.content) as string} 
                />
              </div>
            </div>
          )}
        </For>
        <Show when={isLoading()}>
          <div class="flex justify-start">
            <div class="bg-slate-800/80 rounded-2xl rounded-bl-none p-4 w-16 flex justify-center items-center gap-1 border border-slate-700/50">
              <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </Show>
      </div>

      <div class="p-4 bg-black/20 border-t border-white/10 gap-3 flex flex-col">
        <div class="flex gap-2">
          <input 
            type="text" 
            value={input()}
            onInput={(e) => setInput(e.currentTarget.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask NK AI..."
            class="flex-1 bg-slate-900/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-slate-200 placeholder-slate-500 transition-all placeholder:text-sm shadow-inner"
            disabled={isLoading()}
          />
          <button 
            onClick={sendMessage}
            class="bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 text-white rounded-xl px-5 py-3 transition-all disabled:opacity-50 shadow-lg shadow-blue-500/20 shadow-xl"
            disabled={isLoading() || !input().trim()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </div>
        <div class="flex flex-wrap gap-2">
           <button class="text-[10px] bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 px-3 py-1.5 rounded-lg transition border border-slate-700" onClick={() => { setInput("Give me a health check on next quarter's sales."); sendMessage(); }}>Next Quarter Sales</button>
           <button class="text-[10px] bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 px-3 py-1.5 rounded-lg transition border border-slate-700" onClick={() => { setInput("Where is my cash trapped?"); sendMessage(); }}>Cash Flow Risk</button>
        </div>
      </div>
    </div>
  );
};
