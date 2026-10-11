<script lang="ts">
  import type { Snippet } from 'svelte';
  import '../app.css';

  let { children }: { children: Snippet } = $props();
</script>

<div class="min-h-screen flex flex-col bg-paper-50 text-ink-900 font-serif selection:bg-paper-300">
  <header class="border-b border-paper-300 bg-paper-100 py-4 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-baseline justify-between gap-2">
      <div>
        <h1 class="text-2xl sm:text-3xl font-medium tracking-tight text-ink-950">
          The Manuscript Review
        </h1>
        <p class="font-mono text-xs uppercase tracking-widest text-ink-500 mt-1">
          Linguistic Complexity & Sentiment Evaluation Dispatch
        </p>
      </div>
      <div class="font-mono text-xs text-ink-700 border border-paper-300 px-3 py-1 bg-paper-50">
        API Edition 1.0
      </div>
    </div>
  </header>

  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
    {@render children()}
  </main>

  <footer class="border-t border-paper-300 bg-paper-100 py-6 px-4 sm:px-6 font-mono text-xs text-ink-500 text-center">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
      <span>Offline Architecture: Turso Edge SQLite + Python FastAPI</span>
      <span>Typography: Minimalist Editorial Serif</span>
    </div>
  </footer>
</div>
