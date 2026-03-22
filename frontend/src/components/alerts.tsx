import { For, Show, createSignal } from 'solid-js';
import type { Component } from 'solid-js';

interface AlertType {
  message: string;
  action_type: string;
}

// Global toast state
const [toast, setToast] = createSignal<{ message: string; visible: boolean } | null>(null);

const showToast = (message: string) => {
  setToast({ message, visible: true });
  setTimeout(() => setToast(null), 4000);
};

export const Alerts: Component<{
  alerts: AlertType[];
  onDismiss?: (action_type: string) => void;
}> = (props) => {
  return (
    <>
      {/* Toast Notification */}
      <Show when={toast()?.visible}>
        <div class="fixed top-6 right-6 z-50 animate-[fadeSlideIn_0.3s_ease]">
          <div class="bg-slate-800/95 backdrop-blur-xl border border-green-500/40 text-white px-5 py-4 rounded-2xl shadow-2xl shadow-green-500/20 flex items-center gap-3 max-w-sm">
            <div class="bg-green-500/20 text-green-400 p-2 rounded-xl border border-green-500/30 shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p class="font-semibold text-green-400 text-sm">Action Dispatched</p>
              <p class="text-slate-300 text-xs mt-0.5">{toast()?.message}</p>
            </div>
            <button onClick={() => setToast(null)} class="ml-auto text-slate-500 hover:text-slate-300 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </Show>

      <Show when={props.alerts.length > 0}>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <For each={props.alerts}>
            {(alert) => (
              <div class="bg-white/5 backdrop-blur-md border border-red-500/30 rounded-2xl p-5 shadow-[0_0_15px_rgba(239,68,68,0.1)] flex flex-col justify-between gap-4 group hover:border-red-500/60 transition-colors duration-300">
                <div class="flex items-start gap-3">
                  <div class="bg-red-500/20 text-red-400 p-2 rounded-xl border border-red-500/30 shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-red-400 font-bold text-sm tracking-wider uppercase">Critical Action Items</h3>
                    <p class="text-slate-200 mt-1 font-medium">{alert.message}</p>
                  </div>
                </div>
                
                <div class="flex gap-2 mt-2">
                  <Show when={alert.action_type === 'legal_notice'}>
                    <button
                      onClick={() => { showToast('Legal Notice drafted and queued for dispatch.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-gradient-to-r from-red-600 to-rose-500 hover:from-red-500 hover:to-rose-400 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-red-500/30 flex-1">
                      Draft Legal Notice
                    </button>
                    <button
                      onClick={() => { showToast('Payment reminder sent to customer.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 px-4 py-2 rounded-xl border border-slate-600/50 text-sm font-semibold transition-all flex-1">
                      Send Reminder
                    </button>
                  </Show>
                  
                  <Show when={alert.action_type === 'liquidate_stock'}>
                    <button
                      onClick={() => { showToast('Liquidation schedule raised with warehouse team.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-orange-500/30 flex-1">
                      Schedule Liquidation
                    </button>
                    <button
                      onClick={() => { showToast('Production halt order sent to plant manager.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 px-4 py-2 rounded-xl border border-slate-600/50 text-sm font-semibold transition-all flex-1">
                      Stop Production
                    </button>
                  </Show>
                  
                  <Show when={alert.action_type === 'reconcile_tax'}>
                    <button
                      onClick={() => { showToast('ERP reconciliation job initiated in SAP.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-purple-500/30 flex-1">
                      Reconcile ERP
                    </button>
                    <button
                      onClick={() => { showToast('Alert flagged and escalated to Finance team.'); props.onDismiss?.(alert.action_type); }}
                      class="bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 px-4 py-2 rounded-xl border border-slate-600/50 text-sm font-semibold transition-all flex-1">
                      Flag to Finance
                    </button>
                  </Show>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
    </>
  );
};
