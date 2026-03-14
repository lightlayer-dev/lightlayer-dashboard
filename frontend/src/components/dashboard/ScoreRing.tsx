/**Circular score indicator with color coding.*/

interface ScoreRingProps {
  score: number | null
  size?: number
  className?: string
}

function scoreColor(score: number): string {
  if (score >= 0.7) return "text-green-500"
  if (score >= 0.5) return "text-yellow-500"
  if (score >= 0.3) return "text-orange-500"
  return "text-red-500"
}

function strokeColor(score: number): string {
  if (score >= 0.7) return "#22c55e"
  if (score >= 0.5) return "#eab308"
  if (score >= 0.3) return "#f97316"
  return "#ef4444"
}

export function ScoreRing({ score, size = 64, className = "" }: ScoreRingProps) {
  if (score === null) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
        <span className="text-muted-foreground text-sm">—</span>
      </div>
    )
  }

  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score)

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="currentColor" strokeWidth={4}
          fill="none" className="text-muted/20" />
        <circle cx={size / 2} cy={size / 2} r={radius} stroke={strokeColor(score)} strokeWidth={4}
          fill="none" strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" className="transition-all duration-500" />
      </svg>
      <span className={`absolute text-sm font-bold ${scoreColor(score)}`}>
        {Math.round(score * 100)}%
      </span>
    </div>
  )
}
