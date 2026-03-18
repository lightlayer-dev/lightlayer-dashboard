/**Scan trigger — enter a URL and run agent-bench from the dashboard.*/

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScoreRing } from "./ScoreRing"
import { triggerScan, fetchScanJob, fetchScanJobs, type ScanJob } from "@/lib/api"

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  })
}

function statusBadge(status: ScanJob["status"]) {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    pending: "outline",
    running: "default",
    completed: "secondary",
    failed: "destructive",
  }
  return <Badge variant={variants[status] ?? "outline"}>{status}</Badge>
}

interface Props {
  onScanComplete?: () => void
}

export function ScanTrigger({ onScanComplete }: Props) {
  const [url, setUrl] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<ScanJob[]>([])
  const [pollingIds, setPollingIds] = useState<Set<number>>(new Set())

  // Load recent jobs on mount
  useEffect(() => {
    fetchScanJobs().then(setJobs).catch(() => {})
  }, [])

  // Poll active jobs
  useEffect(() => {
    if (pollingIds.size === 0) return
    const interval = setInterval(async () => {
      for (const id of pollingIds) {
        try {
          const job = await fetchScanJob(id)
          setJobs(prev => prev.map(j => j.id === id ? job : j))
          if (job.status === "completed" || job.status === "failed") {
            setPollingIds(prev => {
              const next = new Set(prev)
              next.delete(id)
              return next
            })
            if (job.status === "completed") onScanComplete?.()
          }
        } catch {}
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [pollingIds, onScanComplete])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return

    setSubmitting(true)
    setError(null)
    try {
      const job = await triggerScan(trimmed)
      setJobs(prev => [job, ...prev])
      setPollingIds(prev => new Set(prev).add(job.id))
      setUrl("")
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const activeJobs = jobs.filter(j => j.status === "pending" || j.status === "running")
  const recentJobs = jobs.filter(j => j.status === "completed" || j.status === "failed").slice(0, 5)

  return (
    <div className="space-y-4">
      {/* URL input */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-semibold mb-3">Scan a Website</h3>
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 px-3 py-2 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              required
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={submitting || !url.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Starting..." : "Scan"}
            </button>
          </form>
          {error && <p className="text-sm text-destructive mt-2">{error}</p>}
        </CardContent>
      </Card>

      {/* Active scans */}
      {activeJobs.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">In Progress</h3>
            <div className="space-y-3">
              {activeJobs.map(job => (
                <div key={job.id} className="flex items-center gap-3 py-2">
                  <div className="w-10 h-10 rounded-full border-2 border-primary flex items-center justify-center">
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{job.url}</p>
                    <p className="text-xs text-muted-foreground">Started {formatDate(job.created_at)}</p>
                  </div>
                  {statusBadge(job.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent completed scans */}
      {recentJobs.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Recent Scans</h3>
            <div className="space-y-3">
              {recentJobs.map(job => (
                <div key={job.id} className="flex items-center gap-3 py-2 border-b last:border-0">
                  {job.status === "completed" && job.overall_score !== null ? (
                    <ScoreRing score={job.overall_score} size={40} />
                  ) : (
                    <div className="w-10 h-10 rounded-full border-2 border-destructive flex items-center justify-center text-destructive text-xs font-bold">!</div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{job.url}</p>
                    <p className="text-xs text-muted-foreground">
                      {job.completed_at ? formatDate(job.completed_at) : formatDate(job.created_at)}
                    </p>
                  </div>
                  {job.status === "completed" && job.overall_score !== null && (
                    <span className="text-sm font-semibold">{Math.round(job.overall_score * 100)}%</span>
                  )}
                  {job.status === "failed" && (
                    <span className="text-xs text-destructive max-w-[200px] truncate">{job.error}</span>
                  )}
                  {statusBadge(job.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
