import type { Component } from 'solid-js';
import { Dashboard } from './components/dashboard';

const App: Component = () => {
  return (
    <div class="h-screen w-full bg-nkPrimary flex flex-col font-sans overflow-hidden">
      <main class="flex-1 overflow-hidden flex">
        <Dashboard />
      </main>
    </div>
  );
};

export default App;
