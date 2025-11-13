"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { resumeApi, jdApi, matchApi, summaryApi, resultsApi, authApi, MatchResultWithSummary, hybridAnalyze } from "@/lib/api"
import { formatScore } from "@/lib/utils"
import { Upload, FileText, Loader2, CheckCircle, XCircle, Save, Info } from "lucide-react"
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

const COLORS = ["#2563eb", "#9333ea", "#10b981", "#f59e0b"]

export default function AnalyzerPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)
  
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState("")
  const [resumeData, setResumeData] = useState<any>(null)
  const [jdData, setJdData] = useState<any>(null)
  const [matchResult, setMatchResult] = useState<MatchResultWithSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [error, setError] = useState("")
  const [summary, setSummary] = useState("")
  const [questions, setQuestions] = useState<string[]>([])
  const [userId, setUserId] = useState<string | null>(null)
  const [semanticMatches, setSemanticMatches] = useState<any[]>([])
  const [graphContext, setGraphContext] = useState<string[]>([])
  const [hybridAnalysis, setHybridAnalysis] = useState("")

  useEffect(() => {
    const getUserId = async () => {
      if (session?.user?.id) {
        setUserId(session.user.id)
      } else if (token) {
        try {
          const response = await authApi.me()
          if (response.success && response.user) {
            setUserId(response.user._id)
          }
        } catch (err) {
          console.error("Failed to get user ID:", err)
        }
      }
    }
    getUserId()
  }, [session, token])

  // Load analysis from localStorage if available (from /analyzer/[id] route)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const loaded = localStorage.getItem("loaded_analysis")
      if (loaded) {
        try {
          const data = JSON.parse(loaded)
          
          // Load resume data
          if (data.resume_data) {
            setResumeData(data.resume_data)
          }
          
          // Load JD data
          if (data.jd_data) {
            setJdData(data.jd_data)
          }
          
          // Set JD text - prefer jd_text from response, fallback to jd_data fields
          if (data.jd_text) {
            setJdText(data.jd_text)
          } else if (data.jd_data) {
            if (data.jd_data.raw_text) {
              setJdText(data.jd_data.raw_text)
            } else if (data.jd_data.profile_text) {
              setJdText(data.jd_data.profile_text)
            }
          }
          
          // Create match result from scores and include skills
          if (data.scores) {
            setMatchResult({
              suitability_score: data.scores.suitability || 0,
              semantic_similarity: data.scores.semantic_similarity || 0,
              skill_overlap: data.scores.skill_overlap || 0,
              experience_relevance: data.scores.experience_relevance || 0,
              resume_data: data.resume_data,
              jd_data: data.jd_data,
              scores: data.scores,
              matching_skills: data.matching_skills || [],
              missing_skills: data.missing_skills || [],
            } as MatchResultWithSummary)
          }
          
          // Load summary if available
          if (data.summary) {
            setSummary(data.summary)
          }
          
          // Load interview questions if available
          if (data.interview_questions && Array.isArray(data.interview_questions)) {
            setQuestions(data.interview_questions)
          }
          
          // Clear loaded_analysis after use
          localStorage.removeItem("loaded_analysis")
        } catch (err) {
          console.error("Failed to parse loaded analysis:", err)
        }
      }
    }
  }, [])

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

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setResumeFile(file)
    setLoading(true)
    setLoadingMessage("Parsing resume...")
    setError("")

    try {
      const response = await resumeApi.parseFile(file)
      if (response.success) {
        setResumeData(response.data)
      } else {
        setError("Failed to parse resume")
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to parse resume")
    } finally {
      setLoading(false)
      setLoadingMessage("")
    }
  }

  const handleJDParse = async () => {
    if (!jdText.trim()) {
      setError("Please enter a job description")
      return
    }

    setLoading(true)
    setLoadingMessage("Parsing job description...")
    setError("")

    try {
      const response = await jdApi.parse(jdText)
      if (response.success) {
        setJdData(response.data)
      } else {
        setError("Failed to parse job description")
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to parse job description")
    } finally {
      setLoading(false)
      setLoadingMessage("")
    }
  }

  const handleMatch = async () => {
    if (!resumeData || !jdData) {
      setError("Please upload a resume and parse a job description first")
      return
    }

    setLoading(true)
    setLoadingMessage("Analyzing with Hybrid Intelligence...")
    setError("")
    setSemanticMatches([])
    setGraphContext([])
    setHybridAnalysis("")

    try {
      // Auto-save result if user is logged in
      const autoSave = !!userId
      const matchResponse = await matchApi.match(resumeData, jdData, undefined, userId, autoSave)
      if (!matchResponse.success) {
        setError("Failed to match resume with job description")
        return
      }

      const result = matchResponse.data as MatchResultWithSummary
      setMatchResult(result)

      // Generate summary
      try {
        const summaryResponse = await summaryApi.generateSummary(result)
        if (summaryResponse.success) {
          setSummary(summaryResponse.summary)
        }
      } catch (err) {
        console.error("Failed to generate summary:", err)
      }

      // Hybrid analysis context
      try {
        const resumePayload = {
          id: resumeData.id || resumeData._id || `resume-${Date.now()}`,
          text: resumeData.raw_text || resumeData.text || resumeData.plain_text || "",
          name: resumeData.name,
          skills: resumeData.skills || resumeData.all_skills || [],
          experiences: resumeData.experience?.map((exp: any) => {
            if (typeof exp === "string") return exp
            if (exp && typeof exp === "object") {
              return [exp.title, exp.company, exp.description, exp.summary].filter(Boolean).join(" - ")
            }
            return ""
          }) || [],
        }

        const jobPayload = {
          id: jdData.id || jdData._id || `job-${Date.now()}`,
          text: jdText || jdData.raw_text || jdData.description || "",
          title: jdData.title || jdData.role || "Job Description",
          skills: jdData.skills_required || jdData.skills || jdData.all_skills || [],
        }

        const hybridResponse = await hybridAnalyze(resumePayload, jobPayload)
        if (hybridResponse) {
          const contextMatches = hybridResponse.context?.semantic_matches || []
          const contextGraph = hybridResponse.context?.graph_context || []
          setSemanticMatches(contextMatches)
          setGraphContext(contextGraph)
          setHybridAnalysis(hybridResponse.analysis || "")
        }
      } catch (hybridErr) {
        console.warn("Hybrid analysis failed, continuing with base analysis:", hybridErr)
        if (!hybridAnalysis && summary) {
          setHybridAnalysis(summary)
        }
      }

      // Generate questions
      try {
        const questionsResponse = await summaryApi.generateQuestions(resumeData, jdData, 10)
        if (questionsResponse.success) {
          setQuestions(questionsResponse.questions || [])
        }
      } catch (err) {
        console.error("Failed to generate questions:", err)
      }

      // Save to localStorage as fallback
      if (result) {
        const contextToSave = {
          matched_skills: result.matching_skills || [],
          missing_skills: result.missing_skills || [],
          role: jdData?.title || "General Role",
          jd_summary: jdData?.raw_text?.substring(0, 500) || jdData?.profile_text?.substring(0, 500) || "",
          resume_data: resumeData,
          jd_data: jdData,
          scores: {
            suitability: result.suitability_score,
            semantic: result.semantic_similarity,
            skills: result.skill_overlap,
            experience: result.experience_relevance,
          },
          timestamp: new Date().toISOString(),
        }
        localStorage.setItem("latest_analysis", JSON.stringify(contextToSave))
        console.log("✅ Analysis context saved to localStorage")
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to match resume")
    } finally {
      setLoading(false)
      setLoadingMessage("")
    }
  }

  const handleSaveResult = async () => {
    if (!userId || !matchResult) return

    try {
      const resultToSave: MatchResultWithSummary = {
        ...matchResult,
        scores: {
          suitability: matchResult.suitability_score || 0,
          semantic_similarity: matchResult.semantic_similarity || 0,
          skill_overlap: matchResult.skill_overlap || 0,
          experience_relevance: matchResult.experience_relevance || 0,
        },
        summary,
        questions,
        matching_skills: matchResult.matching_skills || [],
        missing_skills: matchResult.missing_skills || [],
        resume_data: resumeData,
        jd_data: jdData,
        user_id: userId,
        resume_filename: resumeFile?.name || "Resume",
        jd_title: jdData?.title || "Job Description",
      }

      await resultsApi.saveResult(resultToSave)
      alert("Result saved successfully!")
    } catch (err: any) {
      alert("Failed to save result: " + (err.response?.data?.detail || "Unknown error"))
    }
  }

  // Scores are already in 0-100 range from backend
  const chartData = matchResult
    ? [
        { name: "Suitability", value: Math.max(0, Math.min(100, matchResult.suitability_score || 0)) },
        { name: "Semantic", value: Math.max(0, Math.min(100, matchResult.semantic_similarity || 0)) },
        { name: "Skills", value: Math.max(0, Math.min(100, matchResult.skill_overlap || 0)) },
        { name: "Experience", value: Math.max(0, Math.min(100, matchResult.experience_relevance || 0)) },
      ]
    : []

  // Scores are already in 0-100 range from backend, no need to multiply
  const skillData = matchResult
    ? [
        { name: "Suitability Score", value: Math.max(0, Math.min(100, matchResult.suitability_score || 0)) },
        { name: "Semantic Similarity", value: Math.max(0, Math.min(100, matchResult.semantic_similarity || 0)) },
        { name: "Skill Overlap", value: Math.max(0, Math.min(100, matchResult.skill_overlap || 0)) },
        { name: "Experience Relevance", value: Math.max(0, Math.min(100, matchResult.experience_relevance || 0)) },
      ]
    : []

  return (
    <DashboardLayout
      pageTitle="Resume-JD Analyzer"
      pageDescription="Upload your resume and job description to get a detailed match analysis"
    >
      <div className="space-y-6">
        {error && (
          <Card className="border-destructive bg-destructive/10">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 text-destructive">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Resume Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Resume</CardTitle>
              <CardDescription>Upload your resume (PDF, DOCX, TXT)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-center w-full">
                <label
                  htmlFor="resume-upload"
                  className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-accent"
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-10 h-10 mb-3 text-muted-foreground" />
                    <p className="mb-2 text-sm text-muted-foreground">
                      <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground">PDF, DOCX, or TXT</p>
                  </div>
                  <input
                    id="resume-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx,.txt"
                    onChange={handleResumeUpload}
                    disabled={loading}
                  />
                </label>
              </div>
              {resumeFile && (
                <div className="flex items-center space-x-2 text-sm">
                  <FileText className="h-4 w-4" />
                  <span>{resumeFile.name}</span>
                  {resumeData && <CheckCircle className="h-4 w-4 text-green-500" />}
                </div>
              )}
              {resumeData && (
                <div className="text-sm text-muted-foreground">
                  <p>Name: {resumeData.name || "N/A"}</p>
                  <p>Skills: {resumeData.skills?.length || 0} found</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Job Description */}
          <Card>
            <CardHeader>
              <CardTitle>Job Description</CardTitle>
              <CardDescription>Paste or type the job description</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="jd-text">Job Description Text</Label>
                <Textarea
                  id="jd-text"
                  placeholder="Paste the job description here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  rows={8}
                  disabled={loading}
                />
              </div>
              <Button
                onClick={handleJDParse}
                disabled={loading || !jdText.trim()}
                className="w-full"
                variant="gradient"
              >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {loadingMessage || "Processing..."}
                </>
              ) : (
                "Parse Job Description"
              )}
              </Button>
              {jdData && (
                <div className="text-sm text-muted-foreground">
                  <p>Title: {jdData.title || "N/A"}</p>
                  <p>Skills: {jdData.skills_count || jdData.all_skills?.length || jdData.skills_required?.length || 0} found</p>
                  <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                  Parsed successfully
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Match Button */}
        {resumeData && jdData && (
          <div className="flex justify-center">
            <Button
              onClick={handleMatch}
              disabled={loading}
              size="lg"
              variant="gradient"
              className="px-8"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  {loadingMessage || "Analyzing..."}
                </>
              ) : (
                "Analyze Match"
              )}
            </Button>
          </div>
        )}

        {/* Results */}
        {matchResult && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Match Results</h2>
              {userId && (
                <Button onClick={handleSaveResult} variant="outline">
                  <Save className="mr-2 h-4 w-4" />
                  Save Result
                </Button>
              )}
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Suitability Score</CardDescription>
                  <CardTitle className="text-3xl">
                    {formatScore(matchResult.suitability_score || 0)}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Semantic Similarity</CardDescription>
                  <CardTitle className="text-3xl">
                    {formatScore(matchResult.semantic_similarity || 0)}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Skill Overlap</CardDescription>
                  <CardTitle className="text-3xl">
                    {formatScore(matchResult.skill_overlap || 0)}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Experience Relevance</CardDescription>
                  <CardTitle className="text-3xl">
                    {formatScore(matchResult.experience_relevance || 0)}
                  </CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Score Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={skillData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Score Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value.toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Hybrid Intelligence Insights */}
            {(semanticMatches.length > 0 || graphContext.length > 0 || hybridAnalysis) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      Semantic Context
                      <Info className="h-4 w-4 text-blue-500" />
                    </CardTitle>
                    <CardDescription>Top matches retrieved by the RAG engine</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc pl-5 space-y-2 text-sm text-gray-700 dark:text-gray-300">
                      {semanticMatches && semanticMatches.length > 0 ? (
                        semanticMatches.map((match, idx) => {
                          const text =
                            typeof match === "string"
                              ? match
                              : match?.text || match?.metadata?.snippet || JSON.stringify(match)
                          const score = typeof match === "object" && match?.score !== undefined ? ` (score: ${match.score.toFixed ? match.score.toFixed(4) : match.score})` : ""
                          return (
                            <li key={idx}>
                              {text}
                              {score}
                            </li>
                          )
                        })
                      ) : (
                        <li>No semantic matches found.</li>
                      )}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      Graph Insights (Neo4j)
                      <Info className="h-4 w-4 text-blue-500" />
                    </CardTitle>
                    <CardDescription>Shared skills and relationships from the knowledge graph</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc pl-5 space-y-2 text-sm text-gray-700 dark:text-gray-300">
                      {graphContext && graphContext.length > 0 ? (
                        graphContext.map((skill, idx) => <li key={idx}>{skill}</li>)
                      ) : (
                        <li>No graph insights found yet.</li>
                      )}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}

            {hybridAnalysis && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    Explainability
                    <Info className="h-4 w-4 text-blue-500" />
                  </CardTitle>
                  <CardDescription>
                    This summary blends semantic retrieval and graph reasoning for transparent recommendations.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="max-h-60 overflow-y-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 text-sm text-gray-700 dark:text-gray-200">
                    <p className="whitespace-pre-wrap leading-relaxed">{hybridAnalysis}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Skills Analysis */}
            <Tabs defaultValue="skills" className="w-full">
              <TabsList>
                <TabsTrigger value="skills">Skills</TabsTrigger>
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="questions">Interview Questions</TabsTrigger>
              </TabsList>
              <TabsContent value="skills" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                        Matching Skills
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {matchResult.matching_skills?.map((skill, idx) => (
                          <Badge key={idx} variant="default">
                            {skill}
                          </Badge>
                        )) || <p className="text-muted-foreground">No matching skills found</p>}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <XCircle className="mr-2 h-5 w-5 text-red-500" />
                        Missing Skills
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {matchResult.missing_skills?.map((skill, idx) => (
                          <Badge key={idx} variant="outline">
                            {skill}
                          </Badge>
                        )) || <p className="text-muted-foreground">No missing skills</p>}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              <TabsContent value="summary">
                <Card>
                  <CardHeader>
                    <CardTitle>AI-Generated Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {summary ? (
                      <p className="whitespace-pre-wrap">{summary}</p>
                    ) : (
                      <p className="text-muted-foreground italic">
                        No summary data found. Run a fresh analysis to generate insights.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="questions">
                <Card>
                  <CardHeader>
                    <CardTitle>Interview Questions</CardTitle>
                    <CardDescription>
                      Personalized questions based on your resume and the job description
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {questions && questions.length > 0 ? (
                      <ol className="list-decimal list-inside space-y-2">
                        {questions.map((q, idx) => (
                          <li key={idx} className="text-sm">
                            {q}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="text-muted-foreground italic">
                        No interview questions found. Run a fresh analysis to generate personalized questions.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
