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
