"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { analyticsApi, authApi } from "@/lib/api"
import { formatScore } from "@/lib/utils"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  Brain,
  FileDown,
  Share2,
  Mail,
  Loader2,
  RefreshCw,
  ArrowUp,
  ArrowDown,
} from "lucide-react"

interface AnalyticsSummary {
  total_analyses: number
  latest_match_score: number
  best_match_score: number
  average_skill_overlap: number
  most_matched_role: string
  trend_data: Array<{
    date: string
    match: number
    semantic: number
    skills: number
    experience: number
  }>
  matching_skills_freq: Record<string, number>
  missing_skills_freq: Record<string, number>
  top_roles: Array<{
    title: string
    best_match: number
    average_match: number
    skills: string[]
  }>
  overall_average: {
    suitability: number
    semantic: number
    skills: number
    experience: number
  }
  ai_recommendation: string
}

export default function AnalyticsPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)

  useEffect(() => {
    if (hasAuth) {
      loadSummary()
    }
  }, [hasAuth])

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
    router.push("/login")
    return null
  }

  const loadSummary = async () => {
    try {
      setLoading(true)
      const response = await analyticsApi.getSummary()
      if (response.success) {
        setSummary(response)
      }
    } catch (err) {
      console.error("Failed to load analytics:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerate = async () => {
    setRegenerating(true)
    await loadSummary()
    setRegenerating(false)
  }

  const handleExportPDF = () => {
    window.print()
  }

  const handleExportCSV = () => {
    if (!summary) return
    
    const csvRows = []
    csvRows.push("Date,Match Score,Semantic Similarity,Skill Overlap,Experience Relevance")
    
    summary.trend_data.forEach((row) => {
      csvRows.push(`${row.date},${row.match},${row.semantic},${row.skills},${row.experience}`)
    })
    
    const csvContent = csvRows.join("\n")
    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "resumate-analytics.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <DashboardLayout
        pageTitle="Analytics & Insights"
        pageDescription="Track your resume performance and improvement over time"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading analytics...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!summary || summary.total_analyses === 0) {
    return (
      <DashboardLayout
        pageTitle="Analytics & Insights"
        pageDescription="Track your resume performance and improvement over time"
      >
        <Card className="bg-white rounded-2xl shadow-sm">
          <CardContent className="pt-12 pb-12 text-center">
            <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-semibold mb-2 text-gray-900">No Analytics Data Yet</h3>
            <p className="text-muted-foreground mb-6">
              Run your first analysis to unlock insights!
            </p>
            <Link href="/analyzer">
              <Button variant="gradient" className="bg-gradient-to-r from-blue-500 to-blue-600">
                Run Your First Analysis
              </Button>
            </Link>
          </CardContent>
        </Card>
      </DashboardLayout>
    )
  }

  // Calculate trends
  const skillTrend = summary.trend_data.length > 1
    ? summary.trend_data[summary.trend_data.length - 1].skills - summary.trend_data[0].skills
    : 0
  const semanticTrend = summary.trend_data.length > 1
    ? summary.trend_data[summary.trend_data.length - 1].semantic - summary.trend_data[0].semantic
    : 0

  // Format trend data for charts
  const matchTrendData = summary.trend_data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    match: Math.round(d.match),
    jobTitle: d.date,
  }))

  const categoryTrendData = summary.trend_data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    Suitability: Math.round(d.match),
    Semantic: Math.round(d.semantic),
    Skills: Math.round(d.skills),
    Experience: Math.round(d.experience),
  }))

  // Top skills for charts
  const topMatchingSkills = Object.entries(summary.matching_skills_freq)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([skill, count]) => ({ skill, count }))

  const topMissingSkills = Object.entries(summary.missing_skills_freq)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([skill, count]) => ({ skill, count }))

  return (
    <DashboardLayout
      pageTitle="Analytics & Insights"
      pageDescription="Track your resume performance and improvement over time"
    >
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Section 1: Performance Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Total Analyses</CardDescription>
              <CardTitle className="text-3xl font-semibold text-gray-900">{summary.total_analyses}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Completed resume–JD comparisons</p>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-sm font-medium text-gray-600">Best Match Score</CardDescription>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
              <CardTitle className="text-3xl font-semibold text-gray-900">
                {formatScore(summary.best_match_score)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Best match yet</p>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-600">Most Matched Role</CardDescription>
              <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-2">
                {summary.most_matched_role}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">Your strongest fit</p>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-sm font-medium text-gray-600">Average Skill Overlap</CardDescription>
                {skillTrend > 0 ? (
                  <ArrowUp className="h-4 w-4 text-green-500" />
                ) : skillTrend < 0 ? (
                  <ArrowDown className="h-4 w-4 text-red-500" />
                ) : null}
              </div>
              <CardTitle className="text-3xl font-semibold text-gray-900">
                {formatScore(summary.average_skill_overlap)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500">
                {skillTrend > 0
                  ? `+${skillTrend.toFixed(0)}% since first analysis`
                  : skillTrend < 0
                  ? `${skillTrend.toFixed(0)}% since first analysis`
                  : "No change"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Section 2: Performance Trends */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle>Match Score Over Time</CardTitle>
              <CardDescription>Track your improvement trajectory</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={matchTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis domain={[0, 100]} stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="match"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ fill: "#2563eb", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle>Category Breakdown Trend</CardTitle>
              <CardDescription>Compare all performance dimensions</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={categoryTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis domain={[0, 100]} stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="Suitability"
                    stroke="#1d4ed8"
                    strokeWidth={2}
                    dot={{ fill: "#1d4ed8", r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Semantic"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: "#3b82f6", r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Skills"
                    stroke="#60a5fa"
                    strokeWidth={2}
                    dot={{ fill: "#60a5fa", r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Experience"
                    stroke="#93c5fd"
                    strokeWidth={2}
                    dot={{ fill: "#93c5fd", r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Insight Text */}
        {summary.trend_data.length > 1 && (
          <Card className="bg-gradient-to-r from-blue-50 via-blue-100 to-blue-200 border-blue-200 rounded-2xl">
            <CardContent className="pt-6">
              <p className="text-sm text-gray-700">
                {skillTrend > 0
                  ? `Your skill overlap has improved by ${skillTrend.toFixed(0)}% since your first analysis`
                  : skillTrend < 0
                  ? `Your skill overlap has decreased by ${Math.abs(skillTrend).toFixed(0)}% since your first analysis`
                  : "Your skill overlap has remained consistent"}
                {semanticTrend < 0
                  ? ", while semantic similarity dropped slightly. Try aligning language closer to the job description."
                  : semanticTrend > 0
                  ? ", and semantic similarity has improved. Great job matching job description language!"
                  : "."}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Section 3: Skill Intelligence */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="mr-2 h-5 w-5 text-green-500" />
                Top Matching Skills
              </CardTitle>
              <CardDescription>Skills that frequently appear in your matches</CardDescription>
            </CardHeader>
            <CardContent>
              {topMatchingSkills.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={topMatchingSkills} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis type="number" domain={[0, "dataMax"]} stroke="#6b7280" />
                      <YAxis dataKey="skill" type="category" width={100} stroke="#6b7280" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "white",
                          border: "1px solid #e5e7eb",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {topMatchingSkills.slice(0, 5).map(({ skill, count }) => (
                      <Badge key={skill} variant="secondary" className="bg-green-50 text-green-700">
                        {skill} ({count})
                      </Badge>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground text-sm">No matching skills data available</p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-white rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="mr-2 h-5 w-5 text-orange-500" />
                Top Missing Skills
              </CardTitle>
              <CardDescription>Skills to consider adding to your resume</CardDescription>
            </CardHeader>
            <CardContent>
              {topMissingSkills.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={topMissingSkills} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis type="number" domain={[0, "dataMax"]} stroke="#6b7280" />
                      <YAxis dataKey="skill" type="category" width={100} stroke="#6b7280" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "white",
                          border: "1px solid #e5e7eb",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {topMissingSkills.slice(0, 5).map(({ skill, count }) => (
                      <Badge key={skill} variant="secondary" className="bg-orange-50 text-orange-700">
                        {skill} ({count})
                      </Badge>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground text-sm">No missing skills data available</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* CTA for Enhancer */}
        <div className="flex justify-center">
          <Link href="/enhancer">
            <Button variant="gradient" className="bg-gradient-to-r from-blue-500 to-blue-600">
              Enhance Resume for Missing Skills
            </Button>
          </Link>
        </div>

        {/* Section 4: Role Fit Insights */}
        <Card className="bg-white rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle>Role Fit Insights</CardTitle>
            <CardDescription>Your performance across different job roles</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.top_roles.length > 0 ? (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Role Title</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Best Match</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Avg Match</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Top Skills</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.top_roles.map((role, idx) => (
                        <tr key={idx} className="border-b border-gray-100">
                          <td className="py-3 px-4 font-medium text-gray-900">{role.title}</td>
                          <td className="py-3 px-4">{formatScore(role.best_match)}</td>
                          <td className="py-3 px-4">{formatScore(role.average_match)}</td>
                          <td className="py-3 px-4">
                            <div className="flex flex-wrap gap-1">
                              {role.skills.slice(0, 3).map((skill, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-sm text-gray-600 mt-4">
                  You perform best for roles in {summary.top_roles.slice(0, 2).map(r => r.title).join(" and ")}.
                </p>
              </>
            ) : (
              <p className="text-muted-foreground text-sm">No role data available</p>
            )}
          </CardContent>
        </Card>

        {/* Section 5: Resume Evolution - Placeholder */}
        <Card className="bg-white rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle>Resume Evolution</CardTitle>
            <CardDescription>Compare your resume versions over time</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Compare versions feature coming soon. This will help you track changes in your resume across analyses.
            </p>
          </CardContent>
        </Card>

        {/* Section 6: AI-Powered Recommendations */}
        <Card className="bg-white rounded-2xl shadow-sm border-2 border-blue-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <Brain className="mr-2 h-5 w-5 text-blue-600" />
                  AI Insights
                </CardTitle>
                <CardDescription>Personalized recommendations based on your performance</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRegenerate}
                disabled={regenerating}
              >
                {regenerating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{summary.ai_recommendation}</p>
          </CardContent>
        </Card>

        {/* Section 7: Export & Share */}
        <Card className="bg-white rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle>Export & Share</CardTitle>
            <CardDescription>Download your analytics data or share insights</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button variant="outline" onClick={handleExportPDF} className="flex items-center gap-2">
                <FileDown className="h-4 w-4" />
                Export PDF
              </Button>
              <Button variant="outline" onClick={handleExportCSV} className="flex items-center gap-2">
                <FileDown className="h-4 w-4" />
                Download CSV
              </Button>
              <Button variant="outline" className="flex items-center gap-2" disabled>
                <Share2 className="h-4 w-4" />
                Share via Email
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
