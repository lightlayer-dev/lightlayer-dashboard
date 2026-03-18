/**API client for the LightLayer Dashboard backend.*/

import { authHeaders } from "@/hooks/useAuth"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export interface Site {
  id: number
  url: string
  name: string | null
  created_at: string
  latest_score: number | null
  scan_count: number
}

export interface CheckResult {
  check_name: string
  score: number
}

export interface Scan {
  id: number
  site_id: number
  url: string
  overall_score: number
  source: string
  commit_sha: string | null
  branch: string | null
  created_at: string
  checks: CheckResult[]
}

export interface ScoreTrendPoint {
  date: string
  score: number
  source: string
}

function authedFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  })
}

export async function fetchSites(): Promise<Site[]> {
  const resp = await authedFetch(`${API_BASE}/api/sites/`)
  if (!resp.ok) throw new Error("Failed to fetch sites")
  return resp.json()
}

export async function fetchScoreTrend(siteId: number, limit = 50): Promise<ScoreTrendPoint[]> {
  const resp = await authedFetch(`${API_BASE}/api/sites/${siteId}/trend?limit=${limit}`)
  if (!resp.ok) throw new Error("Failed to fetch trend")
  return resp.json()
}

export async function fetchScan(scanId: number): Promise<Scan> {
  const resp = await authedFetch(`${API_BASE}/api/scans/${scanId}`)
  if (!resp.ok) throw new Error("Failed to fetch scan")
  return resp.json()
}

export async function fetchSite(siteId: number): Promise<Site> {
  const resp = await authedFetch(`${API_BASE}/api/sites/${siteId}`)
  if (!resp.ok) throw new Error("Failed to fetch site")
  return resp.json()
}

export async function fetchSiteScans(siteId: number, limit = 50): Promise<Scan[]> {
  const resp = await authedFetch(`${API_BASE}/api/sites/${siteId}/scans?limit=${limit}`)
  if (!resp.ok) throw new Error("Failed to fetch scans")
  return resp.json()
}
