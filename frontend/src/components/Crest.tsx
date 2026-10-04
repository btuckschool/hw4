// An original shield in the style of Yale's arms (a blue shield with an open book).
// Drawn for this site rather than copied from Yale's trademarked artwork.
export default function Crest({
  size = 40,
  className = '',
  onDark = false,
}: {
  size?: number
  className?: string
  // Adds a white edge so the blue shield stands out on Yale-blue backgrounds.
  onDark?: boolean
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size * 1.2}
      viewBox="0 0 100 120"
      role="img"
      aria-label="Campus Customs crest"
    >
      <path
        d="M8 6 H92 V58 C92 88 72 105 50 116 C28 105 8 88 8 58 Z"
        fill="#00356B"
        stroke={onDark ? '#FFFFFF' : 'none'}
        strokeWidth={onDark ? 5 : 0}
      />
      <path
        d="M14 12 H86 V58 C86 84 68 99 50 109 C32 99 14 84 14 58 Z"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth="2"
        opacity="0.85"
      />
      {/* Open book */}
      <path d="M22 40 Q36 36 49 42 V80 Q36 74 22 78 Z" fill="#FFFFFF" />
      <path d="M78 40 Q64 36 51 42 V80 Q64 74 78 78 Z" fill="#FFFFFF" />
      <g stroke="#00356B" strokeWidth="1.6" strokeLinecap="round" opacity="0.75">
        <path d="M27 50 Q36 47 44 51" />
        <path d="M27 57 Q36 54 44 58" />
        <path d="M27 64 Q36 61 44 65" />
        <path d="M56 51 Q64 47 73 50" />
        <path d="M56 58 Q64 54 73 57" />
        <path d="M56 65 Q64 61 73 64" />
      </g>
      <path d="M50 42 V81" stroke="#00356B" strokeWidth="1.5" />
    </svg>
  )
}
