<script lang="ts">
  import type { Snippet } from 'svelte';
  import '../app.css';
  import EditorialHeader from '$lib/components/layout/EditorialHeader.svelte';
  import EditorialFooter from '$lib/components/layout/EditorialFooter.svelte';

  let { children }: { children: Snippet } = $props();
</script>

<div class="min-h-screen flex flex-col bg-paper-50 text-ink-900 font-serif selection:bg-paper-300">
  <EditorialHeader />
  <main class="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 md:p-6 lg:p-8">
    {@render children()}
  </main>
  <EditorialFooter />
</div>
