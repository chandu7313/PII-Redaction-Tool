interface ConfidenceBarProps {
  value: number; // 0-100
  showLabel?: boolean;
}

/**
 * Confidence meter bar matching the Stitch design.
 * Teal-filled bar with tick marks and ink border.
 */
export default function ConfidenceBar({ value, showLabel = true }: ConfidenceBarProps) {
  const isLow = value < 70;

  return (
    <div className="flex items-center gap-2">
      <div className="tick-bar flex-1">
        <div
          className="tick-fill"
          style={{
            width: `${Math.min(100, Math.max(0, value))}%`,
            opacity: isLow ? 0.7 : 1,
          }}
        />
        <div className="tick-marks" />
      </div>
      {showLabel && (
        <span
          className={`text-xs font-code font-bold min-w-[24px] text-right ${
            isLow ? 'text-stamp-red' : 'text-ink'
          }`}
        >
          {Math.round(value)}
        </span>
      )}
    </div>
  );
}
