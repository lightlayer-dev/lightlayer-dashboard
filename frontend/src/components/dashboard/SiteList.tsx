/**Site list with scores — the main dashboard view.*/

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { ScoreRing } from "./ScoreRing"
import { fetchSites, type Site } from "@/lib/api"

export function SiteList() {
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSites()
      .then(setSites)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading sites...</div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-destructive">Failed to load sites: {error}</p>
          <p className="text-sm text-muted-foreground mt-2">
            Make sure the backend is running at {import.meta.env.VITE_API_URL || "http://localhost:8000"}
          </p>
        </CardContent>
      </Card>
    )
  }

  if (sites.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <h3 className="text-lg font-medium">No sites tracked yet</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Run <code className="bg-muted px-1 py-0.5 rounded text-xs">agent-bench analyze https://your-site.com --output scan.json</code> and POST the result to get started.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-4">
      {sites.map((site) => (
        <Card key={site.id} className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent className="flex items-center gap-6 py-4">
            <ScoreRing score={site.latest_score} size={56} />
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate">{site.name || site.url}</h3>
              <p className="text-sm text-muted-foreground truncate">{site.url}</p>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span>{site.scan_count} scan{site.scan_count !== 1 ? "s" : ""}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
