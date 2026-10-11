<script lang="ts">
  interface Props {
    current?: 'workbench' | 'archive';
  }

  let { current = 'workbench' }: Props = $props();

  const links = [
    { href: '/', label: 'Workbench', key: 'workbench' },
    { href: '/history', label: 'Archive', key: 'archive' }
  ] as const;
</script>

<header class="border-b border-paper-300 bg-paper-100 py-4 px-4 sm:px-6 lg:px-8">
  <div class="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
    <div>
      <h1 class="text-2xl sm:text-3xl font-medium tracking-tight text-ink-950">
        The Manuscript Review
      </h1>
      <p class="font-mono text-xs uppercase tracking-widest text-ink-500 mt-1">
        Linguistic Complexity &amp; Sentiment Evaluation Dispatch
      </p>
    </div>
    <nav class="flex items-center gap-2" aria-label="Primary">
      {#each links as link (link.key)}
        <a
          href={link.href}
          aria-current={current === link.key ? 'page' : undefined}
          class="min-h-[44px] min-w-[44px] inline-flex items-center justify-center px-4 font-mono text-xs uppercase tracking-wider border transition-colors
            {current === link.key
              ? 'bg-ink-950 text-paper-50 border-ink-950'
              : 'bg-paper-50 text-ink-800 border-paper-300'}"
        >
          {link.label}
        </a>
      {/each}
      <span class="hidden sm:inline-block font-mono text-xs text-ink-700 border border-paper-300 px-3 py-2 bg-paper-50 ml-1">
        API Edition 1.0
      </span>
    </nav>
  </div>
</header>
