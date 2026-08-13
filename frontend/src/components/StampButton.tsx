import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface StampButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'danger' | 'default';
  icon?: string;
  rotation?: number;
}

/**
 * Stamp-style button matching the Stitch "rubber stamp" aesthetic.
 * Thick 2px border, slight rotation, scale animation on click.
 */
export default function StampButton({
  children,
  variant = 'default',
  icon,
  rotation = 1,
  className = '',
  ...props
}: StampButtonProps) {
  const variantStyles = {
    primary: 'border-ink bg-ink text-surface-bright hover:bg-surface-tint',
    danger: 'border-stamp-red bg-fresh-paper text-stamp-red hover:bg-stamp-red hover:text-fresh-paper shadow-[2px_2px_0px_#A63D2F]',
    default: 'border-ink bg-fresh-paper text-ink hover:bg-surface-variant',
  };

  return (
    <button
      className={`
        stamp-button border-2 px-6 py-3
        font-headline text-headline-md uppercase
        flex items-center gap-2
        transition-colors cursor-pointer
        ${variantStyles[variant]}
        ${className}
      `}
      style={{ transform: `rotate(${rotation}deg)` }}
      {...props}
    >
      {icon && <span className="material-symbols-outlined">{icon}</span>}
      {children}
    </button>
  );
}
