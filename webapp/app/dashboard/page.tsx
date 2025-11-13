"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { resultsApi, authApi, MatchResultWithSummary } from "@/lib/api"
import { formatDate, formatScore } from "@/lib/utils"
import { 
  Upload, 
  FileText, 
  TrendingUp, 
  Trash2, 
  ExternalLink,
  BarChart3,
  Target,
  Star,
  FileSearch
} from "lucide-react"

export default function DashboardPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [results, setResults] = useState<MatchResultWithSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [userName, setUserName] = useState<string>("User")

  // Check for token on every render
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)

  useEffect(() => {
    const loadData = async () => {
      // Priority 1: Check for token first (faster, doesn't depend on NextAuth)
      if (token) {
        await loadHistory()
        try {
          const userResponse = await authApi.me()
          if (userResponse.success && userResponse.user) {
            setUserName(userResponse.user.name || "User")
          }
        } catch (err) {
          console.error("Failed to get user info:", err)
        }
        return
      }

      // Priority 2: If NextAuth session is authenticated, load data
      if (status === "authenticated" && session?.user?.id) {
        setUserName(session.user.name || "User")
        await loadHistory()
        return
      }

      // Priority 3: If no auth at all and NextAuth has confirmed unauthenticated, redirect
      if (status === "unauthenticated" && !token) {
        router.push("/login")
      }
    }

    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.user?.id, status])

  const loadHistory = async () => {
    try {
      setLoading(true)
      
      let userId = session?.user?.id
      
      if (!userId && token) {
        try {
          const userResponse = await authApi.me()
          if (userResponse.success && userResponse.user) {
            userId = userResponse.user._id
          }
        } catch (err: any) {
          console.error("Failed to get user info:", err)
          if (err?.response?.status === 401) {
            localStorage.removeItem("token")
            router.push("/login")
          }
          setLoading(false)
          return
        }
      }

      if (userId) {
        const response = await resultsApi.getUserHistory(userId)
        if (response.success) {
          setResults(response.results || [])
        }
      } else if (!token) {
        setLoading(false)
      }
    } catch (err) {
      console.error("Failed to load history:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (resultId: string) => {
    if (!window.confirm("Are you sure you want to delete this analysis? This action cannot be undone.")) return

    try {
      await resultsApi.deleteResult(resultId)
      setResults(results.filter((r) => r._id !== resultId))
    } catch (err) {
      alert("Failed to delete result")
    }
  }

  // Auth check
  if (!hasAuth) {
    if (status === "loading") {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading...</p>
          </div>
        </div>
      )
    }
    if (status === "unauthenticated") {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Redirecting to login...</p>
          </div>
        </div>
      )
    }
  }

  const recentResults = results.slice(0, 5)
  
  // Calculate new metrics
  const mostRecentScore = results.length > 0 ? (results[0]?.scores?.suitability || results[0]?.suitability_score || 0) : 0
  const bestMatchScore = results.length > 0 
    ? Math.max(...results.map(r => r.scores?.suitability || r.suitability_score || 0))
    : 0
  const totalAnalyses = results.length
  const lastRole = results.length > 0 
    ? (results[0]?.jd_title || results[0]?.jd_data?.title || "No role analyzed yet")
    : "No role analyzed yet"

  return (
    <DashboardLayout
      pageTitle="Dashboard"
      pageDescription="Welcome back! Here's an overview of your resume analysis progress."
    >
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Most Recent Match Score</CardDescription>
              <CardTitle className="text-3xl font-semibold text-gray-900">{formatScore(mostRecentScore)}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, mostRecentScore)}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">from your latest analysis</div>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Best Match Score</CardDescription>
              <CardTitle className="text-3xl font-semibold text-gray-900">{formatScore(bestMatchScore)}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, bestMatchScore)}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">best match yet</div>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Total Analyses</CardDescription>
              <CardTitle className="text-3xl font-semibold text-gray-900">{totalAnalyses}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-gray-500 dark:text-gray-400">analyses completed</div>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Last Role Analyzed</CardDescription>
              <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-2">{lastRole}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-gray-500 dark:text-gray-400">most recent job target</div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Link href="/analyzer" className="group">
              <div className="flex flex-col items-center justify-center gap-2 bg-white hover:shadow-md transition-all rounded-2xl p-6 cursor-pointer">
                <FileSearch className="h-8 w-8 text-gray-500 group-hover:text-blue-500 transition-colors" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Analyze Resume</span>
              </div>
            </Link>
            <Link href="/enhancer" className="group">
              <div className="flex flex-col items-center justify-center gap-2 bg-white hover:shadow-md transition-all rounded-2xl p-6 cursor-pointer">
                <Upload className="h-8 w-8 text-gray-500 group-hover:text-blue-500 transition-colors" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Enhance Resume</span>
              </div>
            </Link>
            <Link href="/interview" className="group">
              <div className="flex flex-col items-center justify-center gap-2 bg-white hover:shadow-md transition-all rounded-2xl p-6 cursor-pointer">
                <Target className="h-8 w-8 text-gray-500 group-hover:text-blue-500 transition-colors" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Interview Prep</span>
              </div>
            </Link>
            <Link href="/analytics" className="group">
              <div className="flex flex-col items-center justify-center gap-2 bg-white hover:shadow-md transition-all rounded-2xl p-6 cursor-pointer">
                <BarChart3 className="h-8 w-8 text-gray-500 group-hover:text-blue-500 transition-colors" />
                <span className="font-medium text-gray-900 dark:text-gray-100">View Analytics</span>
              </div>
            </Link>
          </div>
        </div>

        {/* Recent Analyses */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Recent Analyses</h2>
            <Link href="/analyzer">
              <Button variant="gradient">
                <Upload className="mr-2 h-4 w-4" />
                New Analysis
              </Button>
            </Link>
          </div>

          {loading ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                <p className="mt-4 text-muted-foreground">Loading analyses...</p>
              </CardContent>
            </Card>
          ) : recentResults.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-muted-foreground mb-4">No analyses yet</p>
                <Link href="/analyzer">
                  <Button variant="gradient">Run Your First Analysis</Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {recentResults.map((result) => (
                <ResultCard key={result._id} result={result} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}

function ResultCard({
  result,
  onDelete,
}: {
  result: MatchResultWithSummary
  onDelete: (id: string) => void
}) {
  const score = result.scores?.suitability || result.suitability_score || 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <span>{result.resume_filename || "Resume"}</span>
              <Badge variant={score > 0.7 ? "default" : score > 0.5 ? "secondary" : "outline"}>
                {formatScore(score)}
              </Badge>
            </CardTitle>
            <CardDescription>
              {result.jd_title || "Job Description"} • {formatDate(result.created_at || "")}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="icon" onClick={() => onDelete(result._id!)}>
              <Trash2 className="h-4 w-4" />
            </Button>
            <Link href={`/analyzer/${result._id}`}>
              <Button variant="ghost" size="icon">
                <ExternalLink className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Suitability</div>
            <div className="font-semibold">{formatScore(result.scores?.suitability || score)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Skills</div>
            <div className="font-semibold">
              {formatScore(result.scores?.skill_overlap || result.skill_overlap || 0)}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Experience</div>
            <div className="font-semibold">
              {formatScore(result.scores?.experience_relevance || result.experience_relevance || 0)}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Semantic</div>
            <div className="font-semibold">
              {formatScore(result.scores?.semantic_similarity || result.semantic_similarity || 0)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
