import { useState } from "react"
import { SiteList } from "@/components/dashboard/SiteList"
import { SiteDetail } from "@/components/dashboard/SiteDetail"

function App() {
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setSelectedSiteId(null)}>
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">LL</span>
            </div>
            <h1 className="text-xl font-semibold">LightLayer</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm text-muted-foreground">
            <a href="https://github.com/lightlayer-dev/agent-bench" target="_blank" rel="noreferrer"
              className="hover:text-foreground transition-colors">
              agent-bench
            </a>
            <a href="https://company.lightlayer.dev/blog" target="_blank" rel="noreferrer"
              className="hover:text-foreground transition-colors">
              Blog
            </a>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-4 py-8">
        {selectedSiteId ? (
          <SiteDetail siteId={selectedSiteId} onBack={() => setSelectedSiteId(null)} />
        ) : (
          <>
            <div className="mb-8">
              <h2 className="text-2xl font-bold">Dashboard</h2>
              <p className="text-muted-foreground mt-1">
                Track your sites' agent-readiness scores over time
              </p>
            </div>
            <SiteList onSelectSite={setSelectedSiteId} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
