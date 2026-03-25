/**Public scan page — scan any URL without signing up.*/

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { ScoreRing } from "@/components/dashboard/ScoreRing"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

interface CheckResult {
  check_name: string
  score: number
  findings: string[]
}

interface ScanResult {
  job_id: number
  url: string
  status: string
  overall_score: number | null
  checks: CheckResult[]
  error: string | null
  created_at: string
  completed_at: string | null
}

function scoreLabel(score: number): { text: string; color: string } {
  if (score >= 0.81) return { text: "Excellent", color: "text-green-500" }
  if (score >= 0.61) return { text: "Good", color: "text-green-400" }
  if (score >= 0.31) return { text: "Needs Work", color: "text-yellow-500" }
  return { text: "Poor", color: "text-red-500" }
}

function formatCheckName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase())
}

function scoreBarColor(score: number): string {
  if (score >= 0.7) return "bg-green-500"
  if (score >= 0.5) return "bg-yellow-500"
  if (score >= 0.3) return "bg-orange-500"
  return "bg-red-500"
}

interface Props {
  onShowAuth: () => void
}

export function PublicScan({ onShowAuth }: Props) {
  const [url, setUrl] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ScanResult | null>(null)
  const [polling, setPolling] = useState(false)
  const [jobId, setJobId] = useState<number | null>(null)

  const pollResult = useCallback(async (id: number) => {
    try {
      const resp = await fetch(`${API_BASE}/api/public/scan/${id}`)
      if (!resp.ok) throw new Error("Failed to fetch results")
      const data: ScanResult = await resp.json()
      setResult(data)
      if (data.status === "completed" || data.status === "failed") {
        setPolling(false)
      }
    } catch {
      // Keep polling on network errors
    }
  }, [])

  useEffect(() => {
    if (!polling || jobId === null) return
    const interval = setInterval(() => pollResult(jobId), 2000)
    return () => clearInterval(interval)
  }, [polling, jobId, pollResult])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    let trimmed = url.trim()
    if (!trimmed) return

    // Auto-add https:// if no protocol
    if (!/^https?:\/\//i.test(trimmed)) {
      trimmed = `https://${trimmed}`
      setUrl(trimmed)
    }

    setSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const resp = await fetch(`${API_BASE}/api/public/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmed }),
      })
      if (resp.status === 429) {
        throw new Error("Rate limit exceeded. Please try again later.")
      }
      if (resp.status === 422) {
        const data = await resp.json()
        throw new Error(data.detail || "Invalid URL")
      }
      if (!resp.ok) throw new Error("Failed to start scan")

      const data = await resp.json()
      setJobId(data.job_id)
      setResult({
        job_id: data.job_id,
        url: trimmed,
        status: data.status,
        overall_score: null,
        checks: [],
        error: null,
        created_at: new Date().toISOString(),
        completed_at: null,
      })
      setPolling(true)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong")
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setUrl("")
    setResult(null)
    setError(null)
    setJobId(null)
    setPolling(false)
  }

  const isScanning = result && (result.status === "pending" || result.status === "running")
  const isDone = result && result.status === "completed"
  const isFailed = result && result.status === "failed"

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">LL</span>
            </div>
            <h1 className="text-xl font-semibold">LightLayer</h1>
          </div>
          <button
            onClick={onShowAuth}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign in
          </button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-16 max-w-3xl">
        {/* Hero */}
        {!isDone && !isFailed && (
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold tracking-tight mb-4">
              How agent-ready is your website?
            </h2>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Find out if AI agents can use your site effectively.
              Free, instant analysis across 8+ dimensions.
            </p>
          </div>
        )}

        {/* Scan input */}
        {!isDone && !isFailed && (
          <Card className="mb-8">
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <input
                  type="text"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  placeholder="Enter a URL — e.g. stripe.com"
                  className="flex-1 px-4 py-3 border rounded-lg bg-background text-base focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={submitting || !!isScanning}
                />
                <button
                  type="submit"
                  disabled={submitting || !url.trim() || !!isScanning}
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-lg text-base font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting ? "Starting..." : isScanning ? "Scanning..." : "Scan"}
                </button>
              </form>
              {error && <p className="text-sm text-destructive mt-3">{error}</p>}
            </CardContent>
          </Card>
        )}

        {/* Scanning progress */}
        {isScanning && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full border-4 border-primary mb-6">
              <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
            <p className="text-lg font-medium mb-2">Analyzing {result.url}...</p>
            <p className="text-sm text-muted-foreground">
              Checking API availability, documentation, structured data, error handling, and more
            </p>
          </div>
        )}

        {/* Results */}
        {isDone && result.overall_score !== null && (
          <div className="space-y-6">
            {/* Score header */}
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground mb-2">Agent-readiness score for</p>
              <p className="text-lg font-semibold mb-6 truncate">{result.url}</p>
              <ScoreRing score={result.overall_score} size={120} className="mx-auto mb-4" />
              <p className={`text-2xl font-bold ${scoreLabel(result.overall_score).color}`}>
                {scoreLabel(result.overall_score).text}
              </p>
              <button
                onClick={handleReset}
                className="mt-4 text-sm text-muted-foreground hover:text-foreground underline transition-colors"
              >
                Scan another site
              </button>
            </div>

            {/* Check breakdown */}
            {result.checks.length > 0 && (
              <Card>
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-4">Score Breakdown</h3>
                  <div className="space-y-4">
                    {result.checks
                      .sort((a, b) => b.score - a.score)
                      .map(check => (
                        <div key={check.check_name}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">{formatCheckName(check.check_name)}</span>
                            <span className="text-sm font-semibold">{Math.round(check.score * 100)}%</span>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${scoreBarColor(check.score)}`}
                              style={{ width: `${Math.round(check.score * 100)}%` }}
                            />
                          </div>
                          {check.findings.length > 0 && (
                            <ul className="mt-2 space-y-1">
                              {check.findings.slice(0, 3).map((finding, i) => (
                                <li key={i} className="text-xs text-muted-foreground pl-2 border-l-2 border-muted">
                                  {finding}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* CTA */}
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="pt-6 text-center">
                <h3 className="text-lg font-semibold mb-2">Track your score over time</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Sign up to monitor your agent-readiness score, get alerts when it changes,
                  and integrate with your CI pipeline.
                </p>
                <button
                  onClick={onShowAuth}
                  className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                  Sign up free
                </button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Failed */}
        {isFailed && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full border-4 border-destructive mb-6">
              <span className="text-destructive text-3xl font-bold">!</span>
            </div>
            <p className="text-lg font-medium mb-2">Scan failed</p>
            <p className="text-sm text-muted-foreground mb-4">
              {result.error || "Something went wrong while scanning this URL."}
            </p>
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-16 py-8 border-t">
          <p className="text-sm text-muted-foreground">
            Powered by{" "}
            <a
              href="https://github.com/lightlayer-dev/agent-bench"
              target="_blank"
              rel="noreferrer"
              className="font-medium text-foreground hover:underline"
            >
              agent-bench
            </a>
            {" "}— the open-source agent-readiness benchmark
          </p>
        </div>
      </main>
    </div>
  )
}
