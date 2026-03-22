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
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <For each={props.alerts}>
            {(alert) => (
              <div class="bg-nkCard border border-white/5 rounded-[1.5rem] p-5 shadow-xl flex flex-col justify-between gap-4 group hover:border-white/20 transition-all duration-300">
                <div class="flex items-start gap-4">
                  <div class="bg-white/10 text-slate-300 p-2.5 rounded-xl border border-white/10 shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-white font-black text-xs">Critical Intelligence Alert</h3>
                    <p class="text-nkText mt-1 font-bold text-sm leading-snug opacity-90">{alert.message}</p>
                  </div>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
  );
};
