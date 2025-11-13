"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter, useParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { resultsApi } from "@/lib/api"
import { Loader2, XCircle } from "lucide-react"

export default function AnalyzerByIdPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const params = useParams()
  const analysisId = params?.id as string
  
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const loadAnalysis = async () => {
      if (!analysisId) {
        setError("No analysis ID provided")
        setLoading(false)
        return
      }

      try {
        const response = await resultsApi.getAnalysis(analysisId)
        if (response.success) {
          // Store in localStorage so the analyzer page can pick it up
          localStorage.setItem("loaded_analysis", JSON.stringify({
            resume_data: response.resume_data,
            jd_data: response.jd_data,
            resume_text: response.resume_text || "",
            jd_text: response.jd_text || "",
            scores: response.scores,
            matching_skills: response.matching_skills || [],
            missing_skills: response.missing_skills || [],
            summary: response.summary || "",
            interview_questions: response.interview_questions || [],
            job_title: response.job_title,
            resume_filename: response.resume_filename,
            created_at: response.created_at,
            analysis_id: analysisId,
          }))
          // Redirect to analyzer page
          router.replace("/analyzer")
        } else {
          setError("Failed to load analysis")
        }
      } catch (err: any) {
        console.error("Error loading analysis:", err)
        setError(err.response?.data?.detail || "Failed to load analysis")
      } finally {
        setLoading(false)
      }
    }

    if (hasAuth && analysisId) {
      loadAnalysis()
    } else if (!hasAuth && status !== "loading") {
      router.push("/login")
    }
  }, [analysisId, hasAuth, status, router])

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
    return null
  }

  if (loading) {
    return (
      <DashboardLayout
        pageTitle="Loading Analysis"
        pageDescription="Loading your analysis..."
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading analysis...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout
        pageTitle="Error"
        pageDescription="Failed to load analysis"
      >
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-destructive">
              <XCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => router.push("/dashboard")}
            >
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </DashboardLayout>
    )
  }

  return null
}

