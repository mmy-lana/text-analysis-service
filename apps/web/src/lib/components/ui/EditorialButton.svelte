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
