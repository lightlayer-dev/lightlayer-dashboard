import { useState } from "react"
import { SiteList } from "@/components/dashboard/SiteList"
import { SiteDetail } from "@/components/dashboard/SiteDetail"
import { ScanTrigger } from "@/components/dashboard/ScanTrigger"
import { ApiKeys } from "@/components/settings/ApiKeys"
import { AuthForm } from "@/components/auth/AuthForm"
import { useAuth } from "@/hooks/useAuth"

type Page = "dashboard" | "settings"

function App() {
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null)
  const [page, setPage] = useState<Page>("dashboard")
  const [refreshKey, setRefreshKey] = useState(0)
  const { user, loading, login, register, logout } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return <AuthForm onLogin={login} onRegister={register} />
  }

  const goHome = () => { setSelectedSiteId(null); setPage("dashboard") }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={goHome}>
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">LL</span>
            </div>
            <h1 className="text-xl font-semibold">LightLayer</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm text-muted-foreground">
            <button
              onClick={goHome}
              className={`hover:text-foreground transition-colors ${page === "dashboard" && !selectedSiteId ? "text-foreground font-medium" : ""}`}
            >
              Dashboard
            </button>
            <button
              onClick={() => { setPage("settings"); setSelectedSiteId(null) }}
              className={`hover:text-foreground transition-colors ${page === "settings" ? "text-foreground font-medium" : ""}`}
            >
              Settings
            </button>
            <a href="https://github.com/lightlayer-dev/agent-bench" target="_blank" rel="noreferrer"
              className="hover:text-foreground transition-colors">
              agent-bench
            </a>
            <span className="text-foreground">{user.name || user.email}</span>
            <button
              onClick={logout}
              className="hover:text-foreground transition-colors"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-4 py-8">
        {page === "settings" ? (
          <div>
            <h2 className="text-2xl font-bold mb-6">Settings</h2>
            <ApiKeys />
          </div>
        ) : selectedSiteId ? (
          <SiteDetail siteId={selectedSiteId} onBack={() => setSelectedSiteId(null)} />
        ) : (
          <>
            <div className="mb-8">
              <h2 className="text-2xl font-bold">Dashboard</h2>
              <p className="text-muted-foreground mt-1">
                Track your sites' agent-readiness scores over time
              </p>
            </div>
            <div className="mb-8">
              <ScanTrigger onScanComplete={() => setRefreshKey(k => k + 1)} />
            </div>
            <SiteList key={refreshKey} onSelectSite={setSelectedSiteId} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
