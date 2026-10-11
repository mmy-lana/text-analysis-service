<script lang="ts">
  import type { Snippet } from 'svelte';

  interface CardProps {
    title?: string;
    caption?: string;
    children: Snippet;
  }

  let { title, caption, children }: CardProps = $props();
</script>

<section class="border border-paper-300 bg-paper-100 p-4 sm:p-6 transition-all">
  {#if title}
    <header class="mb-4 border-b border-paper-200 pb-3">
      <h3 class="font-serif text-lg sm:text-xl font-normal tracking-tight text-ink-950">{title}</h3>
      {#if caption}
        <p class="mt-1 font-mono text-xs uppercase tracking-wider text-ink-500">{caption}</p>
      {/if}
    </header>
  {/if}
  <div>
    {@render children()}
  </div>
</section>
