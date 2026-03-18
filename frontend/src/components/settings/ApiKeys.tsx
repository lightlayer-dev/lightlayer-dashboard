/**API key management — create, list, revoke keys.*/

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  fetchApiKeys, createApiKey, revokeApiKey,
  type ApiKeyInfo, type ApiKeyCreated,
} from "@/lib/api"

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

export function ApiKeys() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [newKeyName, setNewKeyName] = useState("")
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null)
  const [creating, setCreating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadKeys = () => {
    fetchApiKeys()
      .then(setKeys)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(loadKeys, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    setCreating(true)
    setError(null)
    try {
      const key = await createApiKey(newKeyName.trim())
      setCreatedKey(key)
      setNewKeyName("")
      loadKeys()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setCreating(false)
    }
  }

  const handleRevoke = async (keyId: number) => {
    if (!confirm("Revoke this API key? This cannot be undone.")) return
    try {
      await revokeApiKey(keyId)
      loadKeys()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleCopy = () => {
    if (!createdKey) return
    navigator.clipboard.writeText(createdKey.key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return <div className="text-muted-foreground py-8 text-center">Loading API keys...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">API Keys</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Use API keys to submit scan results from agent-bench or CI pipelines.
        </p>
      </div>

      {error && (
        <div className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</div>
      )}

      {/* Created key banner — shown once */}
      {createdKey && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardContent className="py-4">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                  🔑 API key created — copy it now, it won't be shown again!
                </p>
                <code className="text-sm bg-muted px-2 py-1 rounded block break-all font-mono">
                  {createdKey.key}
                </code>
              </div>
              <button
                onClick={handleCopy}
                className="shrink-0 text-sm px-3 py-1.5 rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
              >
                {copied ? "✓ Copied" : "Copy"}
              </button>
            </div>
            <div className="mt-3 text-xs text-muted-foreground space-y-1">
              <p>Use this key to submit scans:</p>
              <code className="block bg-muted px-2 py-1 rounded break-all">
                agent-bench analyze https://example.com --output scan.json
              </code>
              <code className="block bg-muted px-2 py-1 rounded break-all">
                curl -X POST {window.location.origin}/api/scans/ -H "X-API-Key: {createdKey.key}" -H "Content-Type: application/json" -d @scan.json
              </code>
            </div>
            <button
              onClick={() => setCreatedKey(null)}
              className="mt-3 text-xs text-muted-foreground hover:text-foreground"
            >
              Dismiss
            </button>
          </CardContent>
        </Card>
      )}

      {/* Create new key */}
      <Card>
        <CardContent className="py-4">
          <form onSubmit={handleCreate} className="flex gap-3">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., CI Pipeline, Local Dev)"
              className="flex-1 min-w-0 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <button
              type="submit"
              disabled={creating || !newKeyName.trim()}
              className="shrink-0 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {creating ? "Creating..." : "Create Key"}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Key list */}
      {keys.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No API keys yet. Create one to start submitting scans.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {keys.map((k) => (
            <Card key={k.id} className={!k.is_active ? "opacity-50" : ""}>
              <CardContent className="py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{k.name}</span>
                    <code className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                      {k.key_prefix}...
                    </code>
                    {!k.is_active && (
                      <span className="text-xs text-destructive font-medium">Revoked</span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Created {formatDate(k.created_at)}
                    {k.last_used_at && ` · Last used ${formatDate(k.last_used_at)}`}
                  </div>
                </div>
                {k.is_active && (
                  <button
                    onClick={() => handleRevoke(k.id)}
                    className="shrink-0 text-xs px-3 py-1.5 rounded-md border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors"
                  >
                    Revoke
                  </button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
