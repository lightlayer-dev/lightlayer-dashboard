import { useEffect, useState } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchAnalytics, type AnalyticsOverview } from "@/lib/api"

export function AgentTraffic() {
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    setLoading(true)
    fetchAnalytics(undefined, days)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [days])

  if (loading) {
    return <div className="text-muted-foreground py-8 text-center">Loading analytics...</div>
  }

  if (!data || data.total_requests === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-semibold mb-2">No agent traffic yet</h3>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            Install <code className="bg-muted px-1.5 py-0.5 rounded text-xs">@agent-layer/express</code> middleware
            in your app to start tracking AI agent requests.
          </p>
          <pre className="mt-4 bg-muted rounded-lg p-4 text-left text-xs max-w-lg mx-auto overflow-x-auto">
{`import { agentAnalytics } from "@agent-layer/express";

app.use(agentAnalytics({
  endpoint: "https://dash.lightlayer.dev/api/agent-events/",
  apiKey: "your-api-key",
}));`}
          </pre>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex gap-2">
        {[7, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              days === d
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_requests.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Unique Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.unique_agents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Response</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.avg_duration_ms.toFixed(0)}ms</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${data.error_rate > 0.05 ? "text-red-500" : "text-green-500"}`}>
              {(data.error_rate * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Daily traffic chart */}
      {data.daily_traffic.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Daily Agent Traffic</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.daily_traffic}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  className="text-xs"
                  tickFormatter={(d: string) => d.slice(5)} // MM-DD
                />
                <YAxis className="text-xs" />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Agent breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.by_agent.map((agent) => (
              <div key={agent.agent} className="flex items-center justify-between py-2 border-b last:border-0">
                <div className="flex items-center gap-3">
                  <span className="font-medium">{agent.agent}</span>
                  {agent.error_count > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {agent.error_count} errors
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{agent.request_count.toLocaleString()} reqs</span>
                  <span>{agent.avg_duration_ms.toFixed(0)}ms avg</span>
                  <span className="text-xs">
                    {new Date(agent.last_seen).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
