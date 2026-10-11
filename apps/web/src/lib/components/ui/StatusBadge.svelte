<script lang="ts">
  import type { Snippet } from 'svelte';

  interface BadgeProps {
    variant?: 'neutral' | 'positive' | 'warning' | 'negative' | 'accent';
    children: Snippet;
  }

  let { variant = 'neutral', children }: BadgeProps = $props();

  const variantStyles = {
    neutral: 'bg-paper-200 text-ink-800 border-paper-300',
    positive: 'bg-forest-surface text-forest-base border-forest-border',
    warning: 'bg-amber-surface text-amber-base border-amber-border',
    negative: 'bg-vermilion-surface text-vermilion-base border-vermilion-border',
    accent: 'bg-cobalt-surface text-cobalt-base border-cobalt-border'
  };
</script>

<span
  class="inline-flex items-center justify-center min-h-[44px] min-w-[44px] px-3 py-1 border font-mono text-xs uppercase tracking-wider {variantStyles[variant]}"
>
  {@render children()}
</span>
