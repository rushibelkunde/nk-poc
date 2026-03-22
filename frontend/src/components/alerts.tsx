import { For, Show } from 'solid-js';
import type { Component } from 'solid-js';

interface AlertType {
  message: string;
  action_type: string;
}

export const Alerts: Component<{
  alerts: AlertType[];
  onDismiss?: (action_type: string) => void;
}> = (props) => {
  return (
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
                
              </div>
            )}
          </For>
        </div>
      </Show>
  );
};
