"use client"

import { useState, useEffect, Suspense, useRef } from "react"
import { useSession } from "next-auth/react"
import { useRouter, useSearchParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MessageSquare, Send, Loader2, Target, Play, FolderOpen } from "lucide-react"
import { resultsApi, interviewApi, authApi } from "@/lib/api"

function InterviewPrepContent() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const searchParams = useSearchParams()
  const resultId = searchParams.get("result")
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)

  const [questions, setQuestions] = useState<string[]>([])
  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [currentQuestion, setCurrentQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingQuestions, setLoadingQuestions] = useState(false)
  const [resumeData, setResumeData] = useState<any>(null)
  const [jdData, setJdData] = useState<any>(null)
  const [userId, setUserId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<Array<{ session_id: string; role?: string; timestamp?: string }>>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => {
    if (userId) {
      // Auto-load questions from most recent analysis
      loadQuestionsFromRecent()
      // Load existing interview sessions list
      loadSessions()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  useEffect(() => {
    if (resultId && userId) {
      // If specific result ID provided, load that
      loadQuestions()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resultId])

  // Restore local session at mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("interview_session")
      if (saved) {
        try {
          const session = JSON.parse(saved)
          if (Array.isArray(session.questions)) setQuestions(session.questions)
          if (Array.isArray(session.chat_history)) setChatHistory(session.chat_history)
          if (session.session_id) setActiveSessionId(session.session_id)
        } catch {}
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist local session on changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      const payload = { session_id: activeSessionId, questions, chat_history: chatHistory }
      localStorage.setItem("interview_session", JSON.stringify(payload))
    }
  }, [questions, chatHistory, activeSessionId])

  // Auto-save to backend on changes
  useEffect(() => {
    if (!userId) return
    const timeout = setTimeout(async () => {
      try {
        await interviewApi.saveSession(userId, {
          session_id: activeSessionId || undefined,
          role: jdData?.title || "General Role",
          resume_summary: resumeData?.summary,
          jd_summary: jdData?.raw_text?.substring(0, 500) || jdData?.profile_text?.substring(0, 500),
          questions,
          chat_history: chatHistory,
          resume_data: resumeData,
          jd_data: jdData,
        })
      } catch (e) {
        // ignore
      }
    }, 600)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questions, chatHistory, jdData, resumeData, activeSessionId, userId])

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

  const loadQuestionsFromRecent = async () => {
    if (!userId) return

    try {
      setLoadingQuestions(true)
      
      // First, try localStorage fallback
      const localContext = typeof window !== "undefined" ? localStorage.getItem("latest_analysis") : null
      if (localContext) {
        try {
          const parsed = JSON.parse(localContext)
          if (parsed.resume_data) setResumeData(parsed.resume_data)
          if (parsed.jd_data) setJdData(parsed.jd_data)
          console.log("✅ Loaded context from localStorage")
        } catch (e) {
          console.warn("Failed to parse localStorage context:", e)
        }
      }
      
      // Then try API endpoint
      const response = await interviewApi.getInterviewQuestions(userId)
      if (response.success && response.status === "success") {
        if (response.questions && response.questions.length > 0) {
          setQuestions(response.questions)
        }
        if (response.resume_data) {
          setResumeData(response.resume_data)
        }
        if (response.jd_data) {
          setJdData(response.jd_data)
        }
        // Update localStorage with latest data
        if (response.context && typeof window !== "undefined") {
          const contextToSave = {
            ...response.context,
            resume_data: response.resume_data,
            jd_data: response.jd_data,
            timestamp: new Date().toISOString(),
          }
          localStorage.setItem("latest_analysis", JSON.stringify(contextToSave))
        }
      } else if (response.status === "no_context") {
        // No analysis found - check localStorage
        if (localContext) {
          try {
            const parsed = JSON.parse(localContext)
            // Try to generate questions from localStorage data
            if (parsed.resume_data && parsed.jd_data) {
              try {
                const questionsResponse = await interviewApi.generateQuestions(
                  parsed.resume_data,
                  parsed.jd_data,
                  10
                )
                if (questionsResponse.success && questionsResponse.questions) {
                  setQuestions(questionsResponse.questions)
                }
              } catch (e) {
                console.error("Failed to generate questions from localStorage:", e)
              }
            }
          } catch (e) {
            console.warn("Failed to use localStorage context:", e)
          }
        }
      } else {
        // Try to load from history as fallback
        const historyResponse = await resultsApi.getUserHistory(userId)
        if (historyResponse.success && historyResponse.results && historyResponse.results.length > 0) {
          // Get most recent result
          const mostRecent = historyResponse.results[0]
          if (mostRecent.questions && mostRecent.questions.length > 0) {
            setQuestions(mostRecent.questions)
          }
          if (mostRecent.resume_data) {
            setResumeData(mostRecent.resume_data)
          }
          if (mostRecent.jd_data) {
            setJdData(mostRecent.jd_data)
          }
        }
      }
    } catch (err) {
      console.error("Failed to load questions:", err)
      // Final fallback: try localStorage
      const localContext = typeof window !== "undefined" ? localStorage.getItem("latest_analysis") : null
      if (localContext) {
        try {
          const parsed = JSON.parse(localContext)
          if (parsed.resume_data) setResumeData(parsed.resume_data)
          if (parsed.jd_data) setJdData(parsed.jd_data)
        } catch (e) {
          console.warn("Failed to parse localStorage:", e)
        }
      }
    } finally {
      setLoadingQuestions(false)
    }
  }

  const loadQuestions = async () => {
    if (!userId || !resultId) return

    try {
      setLoadingQuestions(true)
      const response = await resultsApi.getUserHistory(userId)
      if (response.success) {
        const result = response.results.find((r: any) => r._id === resultId)
        if (result) {
          if (result.questions) {
            setQuestions(result.questions)
          }
          if (result.resume_data) {
            setResumeData(result.resume_data)
          }
          if (result.jd_data) {
            setJdData(result.jd_data)
          }
        }
      }
    } catch (err) {
      console.error("Failed to load questions:", err)
    } finally {
      setLoadingQuestions(false)
    }
  }

  const handleGenerateQuestions = async () => {
    if (!resumeData || !jdData) {
      alert("Please run an analysis first to generate questions")
      router.push("/analyzer")
      return
    }

    try {
      setLoadingQuestions(true)
      const response = await interviewApi.generateQuestions(resumeData, jdData, 10)
      if (response.success && response.questions) {
        setQuestions(response.questions)
        // Save as a new session explicitly and refresh the list
        if (userId) {
          try {
            const saveRes = await interviewApi.saveSession(userId, {
              role: jdData?.title || "General Role",
              resume_summary: resumeData?.summary,
              jd_summary: jdData?.raw_text?.substring(0, 500) || jdData?.profile_text?.substring(0, 500),
              questions: response.questions,
              chat_history: [],
              resume_data: resumeData,
              jd_data: jdData,
            })
            if (saveRes?.success && saveRes.session_id) {
              setActiveSessionId(saveRes.session_id)
              await loadSessions()
            }
          } catch {}
        }
      }
    } catch (err) {
      console.error("Failed to generate questions:", err)
      alert("Failed to generate questions. Please try again.")
    } finally {
      setLoadingQuestions(false)
    }
  }

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [chatHistory, loading])

  const handleAskQuestion = async () => {
    if (!currentQuestion.trim()) return

    const userMessage = currentQuestion
    setCurrentQuestion("")
    const updatedHistory = [...chatHistory, { role: "user" as const, content: userMessage }]
    setChatHistory(updatedHistory)
    setLoading(true)

    try {
      // Pass userId so backend can auto-fetch context if resumeData/jdData not available
      const response = await interviewApi.mockInterview(
        userMessage,
        resumeData,
        jdData,
        updatedHistory.map(msg => ({ role: msg.role, content: msg.content })),
        userId
      )

      if (response.success) {
        setChatHistory((prev) => [...prev, { role: "assistant", content: response.reply }])
      } else {
        throw new Error("Failed to get response")
      }
    } catch (err: any) {
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: err.response?.data?.detail || "Sorry, I encountered an error. Please try again." },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handlePracticeQuestion = (question: string) => {
    // Set the question in the input and send it
    setCurrentQuestion(question)
    // Small delay to ensure state is set, then send
    setTimeout(() => {
      const updatedHistory = [...chatHistory, { role: "user" as const, content: question }]
      setChatHistory(updatedHistory)
      setCurrentQuestion("")
      setLoading(true)

      interviewApi.mockInterview(
        question,
        resumeData,
        jdData,
        updatedHistory.map(msg => ({ role: msg.role, content: msg.content })),
        userId
      ).then((response) => {
        if (response.success) {
          setChatHistory((prev) => [...prev, { role: "assistant", content: response.reply }])
        }
      }).catch((err: any) => {
        setChatHistory((prev) => [
          ...prev,
          { role: "assistant", content: err.response?.data?.detail || "Sorry, I encountered an error. Please try again." },
        ])
      }).finally(() => {
        setLoading(false)
      })
    }, 100)
  }

  const loadSessions = async () => {
    if (!userId) return
    try {
      const res = await interviewApi.listSessions(userId)
      if (res.success && Array.isArray(res.sessions)) {
        setSessions(res.sessions)
        if (!activeSessionId && res.sessions.length > 0) {
          setActiveSessionId(res.sessions[0].session_id)
          const s = await interviewApi.getSession(userId, res.sessions[0].session_id)
          if (s.success && s.session) {
            setQuestions(s.session.questions || [])
            setChatHistory(s.session.chat_history || [])
            setResumeData(s.session.resume_data || null)
            setJdData(s.session.jd_data || null)
          }
        }
      }
    } catch (e) {
      console.error("Failed to load sessions", e)
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    if (!userId) return
    setActiveSessionId(sessionId)
    try {
      const res = await interviewApi.getSession(userId, sessionId)
      if (res.success && res.session) {
        setQuestions(res.session.questions || [])
        setChatHistory(res.session.chat_history || [])
        setResumeData(res.session.resume_data || null)
        setJdData(res.session.jd_data || null)
        localStorage.setItem("interview_session", JSON.stringify({
          session_id: sessionId,
          questions: res.session.questions || [],
          chat_history: res.session.chat_history || [],
        }))
        // Auto-scroll to bottom after switching
        setTimeout(() => {
          if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: "smooth" })
          }
        }, 50)
      }
    } catch (e) {
      console.error("Failed to fetch session", e)
    }
  }

  return (
    <DashboardLayout
      pageTitle="Interview Preparation"
      pageDescription="Practice interview questions based on your resume and job descriptions"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Questions List */}
          <div className="md:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="mr-2 h-5 w-5" />
                  Interview Questions
                </CardTitle>
                <CardDescription className="flex items-center justify-between">
                  <span>Personalized questions for you</span>
                  <div className="flex items-center space-x-2">
                    <FolderOpen className="h-4 w-4 text-muted-foreground" />
                    <select
                      className="text-xs w-full max-w-md bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm px-2 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                      value={activeSessionId || ""}
                      onChange={(e) => handleSelectSession(e.target.value)}
                    >
                      <option value="" disabled>Select Session</option>
                      {sessions.length > 0 ? (
                        sessions.map((s) => (
                          <option key={s.session_id} value={s.session_id}>
                            {(s.role || "Analysis")} — {s.timestamp ? new Date(s.timestamp).toLocaleString() : ""}
                          </option>
                        ))
                      ) : (
                        <option value="none" disabled>No sessions available</option>
                      )}
                    </select>
                  </div>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loadingQuestions ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-xs text-muted-foreground">
                      Tip: Generate questions from your latest Resume–JD analysis or start a general mock interview.
                    </div>
                    <div className="max-h-96 overflow-y-auto space-y-2">
                      {questions.map((q, idx) => (
                        <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                          <p className="text-sm text-gray-900 dark:text-gray-100 mb-2">{q}</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="w-full text-xs"
                            onClick={() => handlePracticeQuestion(q)}
                          >
                            <Play className="h-3 w-3 mr-1" />
                            Practice in Chat
                          </Button>
                        </div>
                      ))}
                    </div>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={handleGenerateQuestions}
                    >
                      {questions.length ? "Regenerate Questions" : "Generate Questions"}
                    </Button>
                    <Button
                      variant="gradient"
                      className="w-full"
                      onClick={() => router.push("/analyzer")}
                    >
                      Run New Analysis
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Chat Interface */}
          <div className="md:col-span-2">
            <Card className="flex flex-col h-[600px] bg-white dark:bg-gray-800">
              <CardHeader className="border-b border-gray-200 dark:border-gray-700">
                <CardTitle className="flex items-center">
                  <MessageSquare className="mr-2 h-5 w-5" />
                  Mock Interview Chat
                </CardTitle>
                <CardDescription>
                  Ask follow-up questions or practice your answers with AI feedback
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
                {/* Chat Messages Area */}
                <div 
                  ref={chatContainerRef}
                  className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900"
                  style={{ scrollBehavior: "smooth" }}
                >
                  {chatHistory.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center text-muted-foreground">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p className="text-sm font-medium">Start a conversation to practice interview questions</p>
                        <p className="text-xs mt-2 text-gray-500 dark:text-gray-400">
                          Try: &quot;I&apos;d like to practice OOPS questions&quot; or &quot;Ask me about my experience&quot;
                        </p>
                      </div>
                    </div>
                  ) : (
                    <>
                      {chatHistory.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2`}
                        >
                          <div
                            className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
                              msg.role === "user"
                                ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-sm"
                                : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm"
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                          </div>
                        </div>
                      ))}
                      {loading && (
                        <div className="flex justify-start animate-in fade-in">
                          <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200 dark:border-gray-700 shadow-sm">
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                              <span className="text-xs text-gray-500 dark:text-gray-400">AI is thinking...</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                  <div ref={chatEndRef} />
                </div>
                
                {/* Input Area - Sticky at Bottom */}
                <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Ask a question or practice your answer..."
                      value={currentQuestion}
                      onChange={(e) => setCurrentQuestion(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault()
                          handleAskQuestion()
                        }
                      }}
                      className="flex-1 rounded-lg border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500"
                      disabled={loading}
                    />
                    <Button
                      onClick={handleAskQuestion}
                      disabled={loading || !currentQuestion.trim()}
                      variant="gradient"
                      className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-lg px-6"
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default function InterviewPrepPage() {
  return (
    <Suspense fallback={
      <DashboardLayout
        pageTitle="Interview Preparation"
        pageDescription="Loading..."
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </DashboardLayout>
    }>
      <InterviewPrepContent />
    </Suspense>
  )
}
