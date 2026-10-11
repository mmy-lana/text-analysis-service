<script lang="ts">
  import type { Snippet } from 'svelte';

  interface CardProps {
    title?: string;
    caption?: string;
    children: Snippet;
  }

  let { title, caption, children }: CardProps = $props();
</script>

<section class="paper-card border border-paper-300 bg-paper-100 p-4 sm:p-6 transition-all">
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

<style>
  /* Newsprint surface shadow with a deckle (irregular) paper edge. */
  .paper-card {
    box-shadow:
      0 1px 2px rgba(28, 27, 24, 0.06),
      0 4px 12px -2px rgba(28, 27, 24, 0.08),
      0 0 0 1px rgba(222, 216, 199, 0.5) inset,
      1.5px 0 0 -1px var(--color-paper-200),
      -1.5px 0 0 -1px var(--color-paper-200),
      0 1.5px 0 -1px var(--color-paper-200),
      0 -1.5px 0 -1px var(--color-paper-200);
    background-image:
      radial-gradient(ellipse at 20% 10%, rgba(255, 255, 252, 0.6), transparent 55%),
      radial-gradient(ellipse at 85% 90%, rgba(222, 216, 199, 0.35), transparent 50%);
  }
</style>
