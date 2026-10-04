// Handsome Dan, the chat assistant: an original cartoon bulldog in a Yale-blue collar.
export default function DanAvatar({ size = 40, className = '' }: { size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="32" fill="#E6EEF7" />
      {/* Ears */}
      <path d="M9 24 Q10 12 22 15 Q18 20 17 27 Z" fill="#B88A63" />
      <path d="M55 24 Q54 12 42 15 Q46 20 47 27 Z" fill="#B88A63" />
      {/* Head */}
      <ellipse cx="32" cy="33" rx="21" ry="18" fill="#F4EBDF" />
      <ellipse cx="22.5" cy="29.5" rx="6.5" ry="5.5" fill="#D9B48F" />
      <path d="M25 21 Q32 18 39 21" stroke="#C9A27E" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M27 24.5 Q32 22.5 37 24.5" stroke="#C9A27E" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* Eyes */}
      <circle cx="23" cy="30.5" r="2.4" fill="#222" />
      <circle cx="41" cy="30.5" r="2.4" fill="#222" />
      <circle cx="23.8" cy="29.7" r="0.8" fill="#FFF" />
      <circle cx="41.8" cy="29.7" r="0.8" fill="#FFF" />
      {/* Muzzle, nose and underbite */}
      <ellipse cx="32" cy="41" rx="12.5" ry="8" fill="#FBF6EF" />
      <ellipse cx="32" cy="36.5" rx="5" ry="3.2" fill="#2B2B2B" />
      <path d="M32 39.6 V42.5" stroke="#2B2B2B" strokeWidth="1.2" />
      <path d="M24 42.5 Q32 48 40 42.5" stroke="#2B2B2B" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <path d="M26 45 Q32 50.5 38 45 Q32 47.5 26 45 Z" fill="#E9D6C2" stroke="#2B2B2B" strokeWidth="1" />
      <rect x="27.6" y="44.2" width="1.8" height="2.2" rx="0.5" fill="#FFF" />
      <rect x="34.6" y="44.2" width="1.8" height="2.2" rx="0.5" fill="#FFF" />
      {/* Yale-blue collar with a Y tag */}
      <path d="M15 49 Q32 59 49 49 L49 54 Q32 64 15 54 Z" fill="#00356B" />
      <circle cx="32" cy="58" r="3.6" fill="#FFFFFF" stroke="#00356B" strokeWidth="1" />
      <text x="32" y="60.2" textAnchor="middle" fontSize="5.5" fontWeight="700" fill="#00356B" fontFamily="Georgia, serif">
        Y
      </text>
    </svg>
  )
}
