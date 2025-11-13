"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Sparkles, Copy, Check, Loader2 } from "lucide-react"
import { enhanceApi, resultsApi } from "@/lib/api"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function EnhancerPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)

  const [inputText, setInputText] = useState("")
  const [outputText, setOutputText] = useState("")
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [enhancementStyle, setEnhancementStyle] = useState("ats-friendly")
  const [userId, setUserId] = useState<string | null>(null)
  const [jdOptions, setJdOptions] = useState<Array<{ id: string; title: string; analyzed_at: string; jd_id?: string; jd_text?: string }>>([])
  const [selectedJdId, setSelectedJdId] = useState<string>("")
  const [jdSummary, setJdSummary] = useState<string>("")

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

  useEffect(() => {
    const fetchUserAndJDs = async () => {
      try {
        const me = await fetchUserId()
        if (!me) return
        setUserId(me)
        const history = await resultsApi.getUserHistory(me)
        if (history.success && Array.isArray(history.results)) {
          const options = history.results
            .map((r: any) => ({
              id: r._id,
              title: r.jd_data?.title || "Job Description",
              analyzed_at: r.created_at || "",
              jd_id: r.jd_id,
              jd_text: r.jd_data?.raw_text || r.jd_data?.profile_text || r.jd_data?.description || "",
            }))
            .sort((a: any, b: any) => (b.analyzed_at || "").localeCompare(a.analyzed_at || ""))
          setJdOptions(options)
        }
      } catch (e) {
        // ignore
      }
    }
    fetchUserAndJDs()
  }, [])

  const fetchUserId = async (): Promise<string | null> => {
    try {
      const me = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || "http://localhost:8000"}/auth/me`, {
        headers: typeof window !== "undefined" && localStorage.getItem("token") ? { Authorization: `Bearer ${localStorage.getItem("token")}` } : {},
      })
      const data = await me.json()
      return data?.user?._id || null
    } catch {
      return null
    }
  }

  const handleEnhance = async () => {
    if (!inputText.trim()) {
      alert("Please enter some text to enhance")
      return
    }

    if (enhancementStyle === "jd-aligned" && !selectedJdId) {
      alert("⚠️ Please select a job description first to tailor your resume.")
      return
    }

    setLoading(true)
    setOutputText("")

    try {
      let response
      if (enhancementStyle === "jd-aligned") {
        response = await enhanceApi.enhanceWithJD(userId as string, selectedJdId || null, "jd-aligned", inputText)
      } else {
        // map UI values to backend accepted styles
        const style = enhancementStyle as "ats-friendly" | "professional" | "concise"
        response = await enhanceApi.enhance(inputText, style)
      }

      if (response.success) {
        setOutputText(response.enhanced_text)
      } else {
        alert("Failed to enhance resume section")
      }
    } catch (err: any) {
      console.error("Enhancement error:", err)
      alert(err.response?.data?.detail || "Failed to enhance resume. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(outputText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <DashboardLayout
      pageTitle="AI Resume Tailoring"
      pageDescription="Tailor your resume section to a specific job description from your analysis history"
    >
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-6">
        {/* JD Selector */}
        <Card>
          <CardHeader>
            <CardTitle>Select Job Description</CardTitle>
            <CardDescription>Choose a previously analyzed JD to tailor your resume</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {jdOptions.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No previous analyses found. Please analyze your resume and JD in the Analyzer page first.
              </div>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <label className="text-sm w-40">Target JD</label>
                  <select
                    className="text-sm w-full max-w-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                    value={selectedJdId}
                    onChange={(e) => {
                      const id = e.target.value
                      setSelectedJdId(id)
                      const found = jdOptions.find((o) => o.id === id)
                      const title = found?.title || "Role"
                      const focus = found?.jd_text ? (found.jd_text.slice(0, 160) + (found.jd_text.length > 160 ? "..." : "")) : ""
                      setJdSummary(`Target Job: ${title}${focus ? `\nFocus: ${focus}` : ""}`)
                    }}
                  >
                    <option value="">Select Job Description</option>
                    {jdOptions.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.title} — {o.analyzed_at ? new Date(o.analyzed_at).toLocaleString() : ""}
                      </option>
                    ))}
                  </select>
                </div>
                {jdSummary && (
                  <pre className="text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-3">
                    {jdSummary}
                  </pre>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Enhancement Style Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Enhancement Mode</CardTitle>
            <CardDescription>Choose how you want to enhance your resume</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={enhancementStyle} onValueChange={setEnhancementStyle}>
              <TabsList>
                <TabsTrigger value="ats-friendly">ATS-Friendly</TabsTrigger>
                <TabsTrigger value="professional">Professional</TabsTrigger>
                <TabsTrigger value="concise">Concise</TabsTrigger>
                <TabsTrigger value="jd-aligned">JD-Aligned</TabsTrigger>
              </TabsList>
              <TabsContent value="ats-friendly" className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Optimizes for Applicant Tracking Systems with standard keywords and formatting.
                </p>
              </TabsContent>
              <TabsContent value="professional" className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Enhances for professional tone and clarity while maintaining formality.
                </p>
              </TabsContent>
              <TabsContent value="concise" className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Makes the text more concise while preserving all key information.
                </p>
              </TabsContent>
              <TabsContent value="jd-aligned" className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Tailor this section to match the selected job description. Please select a JD above before enhancing.
                </p>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Original Text</CardTitle>
              <CardDescription>Paste your resume section here</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="input-text">Resume Section</Label>
                <Textarea
                  id="input-text"
                  placeholder="Paste your resume section here..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  rows={12}
                  className="font-mono text-sm"
                />
              </div>
              <Button
                onClick={handleEnhance}
                disabled={loading || !inputText.trim()}
                variant="gradient"
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Enhancing...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Enhance
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Enhanced Text</CardTitle>
              <CardDescription>ATS-friendly, optimized version</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="output-text">Enhanced Resume Section</Label>
                  {outputText && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopy}
                      className="h-8"
                    >
                      {copied ? (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                  )}
                </div>
                <Textarea
                  id="output-text"
                  value={outputText || "Enhanced text will appear here..."}
                  readOnly
                  rows={12}
                  className="font-mono text-sm bg-muted"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Tips for Better Results</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
              <li>Use action verbs (e.g., &quot;Developed&quot;, &quot;Implemented&quot;, &quot;Led&quot;)</li>
              <li>Include quantifiable achievements and metrics</li>
              <li>Use keywords relevant to your target job</li>
              <li>Keep sentences concise and clear</li>
              <li>Avoid jargon and acronyms unless industry-standard</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
