interface StatusChipProps {
  label: string;
  variant?: 'danger' | 'success' | 'neutral';
  rotation?: number;
}

/**
 * Status chip matching the Stitch "classified stamp" aesthetic.
 * Rotated border with all-caps Courier Prime text.
 */
export default function StatusChip({
  label,
  variant = 'danger',
  rotation = -2,
}: StatusChipProps) {
  const variantStyles = {
    danger: 'border-stamp-red text-stamp-red',
    success: 'border-olive text-olive',
    neutral: 'border-ink text-ink',
  };

  return (
    <div
      className={`
        border-2 px-3 py-1
        font-label text-label-caps uppercase
        tracking-widest font-bold
        inline-block
        ${variantStyles[variant]}
      `}
      style={{ transform: `rotate(${rotation}deg)` }}
    >
      {label}
    </div>
  );
}
