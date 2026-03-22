import type { Component } from 'solid-js';
import { Dashboard } from './components/dashboard';

const App: Component = () => {
  return (
    <div class="h-screen w-full bg-gray-50 flex flex-col font-sans overflow-hidden">
      {/* <header class="bg-nkPrimary text-white p-4 flex items-center justify-between shadow-md z-10">
        <div class="flex items-center gap-3">
          <div class="text-2xl font-bold tracking-wider">NK PROTEIN</div>
          <div class="text-sm bg-nkAccent text-white px-2 py-1 rounded font-semibold ml-4">
            COMMAND CENTER
          </div>
        </div>
        <div class="text-sm opacity-80">Welcome, CMD</div>
      </header> */}
      
      <main class="flex-1 overflow-hidden flex">
        <Dashboard />
      </main>
    </div>
  );
};

export default App;
