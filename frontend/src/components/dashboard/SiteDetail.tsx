/**Site detail view — per-check breakdown + score trend chart.*/

import { useEffect, useState } from "react"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell,
} from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import { ScoreRing } from "./ScoreRing"
import { Badge } from "@/components/ui/badge"
import {
  fetchSite, fetchSiteScans, fetchScoreTrend,
  type Site, type Scan, type ScoreTrendPoint,
} from "@/lib/api"

function scoreColor(score: number): string {
  if (score >= 0.8) return "#22c55e"
  if (score >= 0.5) return "#eab308"
  return "#ef4444"
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  })
}

interface Props {
  siteId: number
  onBack: () => void
}

export function SiteDetail({ siteId, onBack }: Props) {
  const [site, setSite] = useState<Site | null>(null)
  const [scans, setScans] = useState<Scan[]>([])
  const [trend, setTrend] = useState<ScoreTrendPoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetchSite(siteId),
      fetchSiteScans(siteId),
      fetchScoreTrend(siteId),
    ])
      .then(([s, sc, t]) => { setSite(s); setScans(sc); setTrend(t) })
      .finally(() => setLoading(false))
  }, [siteId])

  if (loading) {
    return <div className="flex items-center justify-center py-12 text-muted-foreground">Loading...</div>
  }

  if (!site) {
    return <div className="text-destructive py-12 text-center">Site not found</div>
  }

  const latestScan = scans[0] ?? null
  const trendData = [...trend].reverse().map(p => ({
    date: formatDate(p.date),
    score: Math.round(p.score * 100),
    source: p.source,
  }))

  const checkData = latestScan?.checks.map(c => ({
    name: c.check_name,
    score: Math.round(c.score * 100),
    raw: c.score,
  })) ?? []

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <div>
        <button onClick={onBack} className="text-sm text-muted-foreground hover:text-foreground mb-4 flex items-center gap-1">
          ← Back to sites
        </button>
        <div className="flex items-center gap-4">
          <ScoreRing score={site.latest_score} size={64} />
          <div>
            <h2 className="text-2xl font-bold">{site.name || site.url}</h2>
            <p className="text-sm text-muted-foreground">{site.url} · {site.scan_count} scan{site.scan_count !== 1 ? "s" : ""}</p>
          </div>
        </div>
      </div>

      {/* Score Trend */}
      {trendData.length > 1 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Score Trend</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} className="text-muted-foreground" />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip formatter={(v) => `${Number(v)}%`} />
                <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Per-Check Breakdown */}
      {checkData.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Check Breakdown (Latest Scan)</h3>
            <ResponsiveContainer width="100%" height={Math.max(200, checkData.length * 48)}>
              <BarChart data={checkData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 13 }} width={80} />
                <Tooltip formatter={(v) => `${Number(v)}%`} />
                <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={24}>
                  {checkData.map((entry, i) => (
                    <Cell key={i} fill={scoreColor(entry.raw)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Scan History */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-4">Scan History</h3>
          <div className="space-y-3">
            {scans.map((scan) => (
              <div key={scan.id} className="flex items-center gap-4 py-2 border-b last:border-0">
                <ScoreRing score={scan.overall_score} size={40} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{Math.round(scan.overall_score * 100)}%</span>
                    <Badge variant="secondary" className="text-xs">{scan.source}</Badge>
                    {scan.branch && <span className="text-xs text-muted-foreground">{scan.branch}</span>}
                  </div>
                  <p className="text-xs text-muted-foreground">{formatDate(scan.created_at)}</p>
                </div>
                <div className="flex gap-1">
                  {scan.checks.map((c) => (
                    <div
                      key={c.check_name}
                      title={`${c.check_name}: ${Math.round(c.score * 100)}%`}
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: scoreColor(c.score) }}
                    />
                  ))}
                </div>
              </div>
            ))}
            {scans.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">No scans yet</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
