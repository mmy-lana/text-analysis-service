### Design System: Minimalist Editorial Paper Serif

The visual aesthetic evokes historical print journalism, broadsheets, and editorial journals. The palette uses an unbleached parchment/paper base, deep printer's ink typography, razor-thin framing rules, and restrained pigment accents for analytic status indications.

#### Tailwind CSS v4 Theme Token Directives (`apps/web/src/app.css`)

```css
@import "tailwindcss";

@theme {
  --color-paper-50: #fbfbf9;
  --color-paper-100: #f7f5ef;
  --color-paper-200: #eeeae0;
  --color-paper-300: #dfd8c7;
  --color-paper-400: #cec3ab;

  --color-ink-950: #121210;
  --color-ink-900: #1c1b18;
  --color-ink-800: #2d2b27;
  --color-ink-700: #46433d;
  --color-ink-500: #736f65;
  --color-ink-300: #aba598;

  --color-vermilion-base: #a82e2e;
  --color-vermilion-surface: #f9ebeb;
  --color-vermilion-border: #dca8a8;

  --color-amber-base: #9a6700;
  --color-amber-surface: #fcf4e6;
  --color-amber-border: #e3caa0;

  --color-forest-base: #22593d;
  --color-forest-surface: #edf5f0;
  --color-forest-border: #a4ceb5;

  --color-cobalt-base: #204569;
  --color-cobalt-surface: #edf3f8;
  --color-cobalt-border: #9fbdd6;

  --font-serif: "Newsreader", "Charis SIL", "Georgia", "Cambria", serif;
  --font-mono: "JetBrains Mono", "Courier New", monospace;
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;

  --spacing-touch: 44px;
}

@utility bg-paper-50 { background-color: var(--color-paper-50); }
@utility bg-paper-100 { background-color: var(--color-paper-100); }
@utility bg-paper-200 { background-color: var(--color-paper-200); }
@utility bg-paper-300 { background-color: var(--color-paper-300); }
@utility bg-paper-400 { background-color: var(--color-paper-400); }
@utility border-paper-200 { border-color: var(--color-paper-200); }
@utility border-paper-300 { border-color: var(--color-paper-300); }
@utility border-paper-400 { border-color: var(--color-paper-400); }
@utility bg-ink-950 { background-color: var(--color-ink-950); }
@utility bg-ink-800 { background-color: var(--color-ink-800); }
@utility text-ink-950 { color: var(--color-ink-950); }
@utility text-ink-900 { color: var(--color-ink-900); }
@utility text-ink-800 { color: var(--color-ink-800); }
@utility text-ink-700 { color: var(--color-ink-700); }
@utility text-ink-500 { color: var(--color-ink-500); }
@utility text-ink-300 { color: var(--color-ink-300); }
@utility text-paper-50 { color: var(--color-paper-50); }
@utility text-paper-400 { color: var(--color-paper-400); }
@utility border-ink-950 { border-color: var(--color-ink-950); }
@utility border-ink-700 { border-color: var(--color-ink-700); }
@utility bg-vermilion-surface { background-color: var(--color-vermilion-surface); }
@utility text-vermilion-base { color: var(--color-vermilion-base); }
@utility border-vermilion-border { border-color: var(--color-vermilion-border); }
@utility bg-amber-surface { background-color: var(--color-amber-surface); }
@utility text-amber-base { color: var(--color-amber-base); }
@utility border-amber-border { border-color: var(--color-amber-border); }
@utility bg-forest-surface { background-color: var(--color-forest-surface); }
@utility text-forest-base { color: var(--color-forest-base); }
@utility border-forest-border { border-color: var(--color-forest-border); }
@utility bg-cobalt-surface { background-color: var(--color-cobalt-surface); }
@utility text-cobalt-base { color: var(--color-cobalt-base); }
@utility border-cobalt-border { border-color: var(--color-cobalt-border); }

:root {
  background-color: var(--color-paper-50);
  color: var(--color-ink-900);
  font-family: var(--font-serif);
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

* {
  box-sizing: border-box;
}

*:focus-visible {
  outline: 2px solid var(--color-ink-950);
  outline-offset: 2px;
}
```

### Responsive Matrix Specifications

- Viewport 360px (Compact Mobile): Single-column continuous layout. Header elements collapse into stacked title and action rows. Analysis controls stack with 100% width. Metric indicators render as single-value tabular rows. Padding is bounded to `12px` (`px-3`).
- Viewport 390px (Standard Mobile): Single-column continuous layout. Padding expands to `16px` (`px-4`). Metric gauges display stacked title and inline value badges.
- Viewport 430px (Large Mobile): Single-column layout. Metric highlights display as a 2-column grid. Button groups align horizontally when holding fewer than 3 items.
- Viewport 768px (Tablet): Dual-column split begins. Top area displays document input box with integrated status toolbar. Bottom metrics display in a 3-column analysis grid. Margins scale to `24px` (`px-6`).
- Viewport 1024px+ (Desktop): Side-by-side broadsheet split layout. Left pane (60% width) hosts the editorial composition textarea and sentence-level highlighter. Right pane (40% width) provides a sticky reading deck containing sentiment meters and readability gauges. Margins scale to `32px` (`px-8`).

Touch Target Rule: All interactive controls must explicitly specify `min-h-[44px]` and `min-w-[44px]` with zero reliance on hover-triggered interfaces.

---

### Atomic Components

#### `apps/web/src/lib/components/ui/EditorialButton.svelte`

```svelte
<script lang="ts">
  import type { Snippet } from 'svelte';

  interface ButtonProps {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    fullWidth?: boolean;
    onclick?: (e: MouseEvent) => void;
    children: Snippet;
  }

  let {
    variant = 'primary',
    type = 'button',
    disabled = false,
    fullWidth = false,
    onclick,
    children
  }: ButtonProps = $props();
</script>

<button
  {type}
  {disabled}
  {onclick}
  class="editorial-button"
  class:variant-primary={variant === 'primary'}
  class:variant-secondary={variant === 'secondary'}
  class:variant-ghost={variant === 'ghost'}
  class:variant-danger={variant === 'danger'}
  class:w-full={fullWidth}
>
  {@render children()}
</button>

<style>
  .editorial-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    line-height: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    min-height: var(--spacing-touch);
    min-width: var(--spacing-touch);
    padding: 0.625rem 1.25rem;
    transition-property: color, background-color, border-color, transform;
    transition-duration: 150ms;
    border-width: 1px;
    border-style: solid;
    user-select: none;
  }

  .editorial-button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .editorial-button:active:not(:disabled) {
    transform: translateY(1px);
  }

  .variant-primary {
    background-color: var(--color-ink-950);
    color: var(--color-paper-50);
    border-color: var(--color-ink-950);
  }
  .variant-primary:active:not(:disabled) {
    background-color: var(--color-ink-800);
  }

  .variant-secondary {
    background-color: var(--color-paper-100);
    color: var(--color-ink-900);
    border-color: var(--color-paper-300);
  }
  .variant-secondary:active:not(:disabled) {
    background-color: var(--color-paper-200);
    border-color: var(--color-ink-700);
  }

  .variant-ghost {
    background-color: transparent;
    color: var(--color-ink-800);
    border-color: transparent;
  }
  .variant-ghost:active:not(:disabled) {
    background-color: var(--color-paper-200);
    border-color: var(--color-paper-300);
  }

  .variant-danger {
    background-color: var(--color-vermilion-surface);
    color: var(--color-vermilion-base);
    border-color: var(--color-vermilion-border);
  }
  .variant-danger:active:not(:disabled) {
    background-color: var(--color-vermilion-base);
    color: var(--color-paper-50);
  }
</style>
```

#### `apps/web/src/lib/components/ui/EditorialTextarea.svelte`

```svelte
<script lang="ts">
  interface TextareaProps {
    value: string;
    placeholder?: string;
    id?: string;
    name?: string;
    required?: boolean;
    rows?: number;
    disabled?: boolean;
    oninput: (val: string) => void;
  }

  let {
    value,
    placeholder = 'Enter or paste manuscript text for evaluation...',
    id = 'manuscript-input',
    name = 'manuscript',
    required = false,
    rows = 12,
    disabled = false,
    oninput
  }: TextareaProps = $props();

  function handleInput(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    oninput(target.value);
  }
</script>

<div class="relative w-full border border-paper-300 bg-paper-100 p-3 sm:p-4">
  <label for={id} class="sr-only">Manuscript Body</label>
  <textarea
    {id}
    {name}
    {required}
    {rows}
    {disabled}
    {placeholder}
    value={value}
    oninput={handleInput}
    class="w-full resize-y bg-transparent font-serif text-base sm:text-lg leading-relaxed text-ink-950 placeholder-ink-500 outline-none border-0 p-0 focus:ring-0 disabled:opacity-50 min-h-[160px]"
  ></textarea>
  <div class="mt-2 flex items-center justify-between border-t border-paper-200 pt-2 font-mono text-[11px] text-ink-500 uppercase">
    <span>Format: Plain Text</span>
    <span>{value.length} characters</span>
  </div>
</div>
```

#### `apps/web/src/lib/components/ui/PaperCard.svelte`

```svelte
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
```

#### `apps/web/src/lib/components/ui/StatusBadge.svelte`

```svelte
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
```

#### `apps/web/src/lib/components/ui/MetricGauge.svelte`

```svelte
<script lang="ts">
  interface MetricGaugeProps {
    label: string;
    value: number;
    min?: number;
    max?: number;
    unit?: string;
    interpretation?: string;
  }

  let {
    label,
    value,
    min = 0,
    max = 100,
    unit = '',
    interpretation = ''
  }: MetricGaugeProps = $props();

  let percentage = $derived(
    Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100)
  );
</script>

<div class="border border-paper-300 bg-paper-50 p-4">
  <div class="flex items-baseline justify-between mb-2">
    <span class="font-mono text-xs uppercase tracking-wider text-ink-500">{label}</span>
    <span class="font-serif text-2xl font-medium text-ink-950">
      {value.toFixed(1)}{unit}
    </span>
  </div>
  <div class="relative h-2 w-full bg-paper-200 overflow-hidden border border-paper-300">
    <div
      class="h-full bg-ink-950 transition-all duration-300 ease-out"
      style="width: {percentage}%"
    ></div>
  </div>
  {#if interpretation}
    <p class="mt-2 font-mono text-[11px] text-ink-700 tracking-tight">{interpretation}</p>
  {/if}
</div>
```
