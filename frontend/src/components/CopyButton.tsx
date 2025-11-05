import { useState } from 'react';

function CopyIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" {...props}>
      <path d="M8 7a3 3 0 0 1 3-3h7a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3h-7a3 3 0 0 1-3-3V7Z" stroke="currentColor" fill="none" strokeWidth="1.5"/>
      <path d="M4 10v7a3 3 0 0 0 3 3h7" stroke="currentColor" fill="none" strokeWidth="1.5"/>
    </svg>
  );
}
function CheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" {...props}>
      <path d="m5 13 4 4L19 7" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function CopyButton({
  text,
  className = '',
  label = 'Скопировать',
}: {
  text: string;
  className?: string;
  label?: string;
}) {
  const [ok, setOk] = useState(false);
  const disabled = !text || !text.trim();

  const onCopy = async () => {
    if (disabled) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } finally { document.body.removeChild(ta); }
    }
    setOk(true);
    setTimeout(() => setOk(false), 1200);
  };

  return (
    <button
      type="button"
      onClick={onCopy}
      disabled={disabled}
      className={
        `p-1 rounded-md transition focus:outline-none focus:ring-2 focus:ring-primary-500 
         ${disabled ? 'opacity-40 cursor-not-allowed' : 'hover:bg-black/10'} ` + className
      }
      title={ok ? 'Скопировано!' : label}
      aria-label={label}
    >
      {ok ? <CheckIcon /> : <CopyIcon />}
    </button>
  );
}
