"use client"

import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Rocket, Brain, ExternalLink } from "lucide-react"

export default function ResourcesPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const hasAuth = token || (status === "authenticated" && session)

  useEffect(() => {
    if (!hasAuth && status !== "loading") {
      router.push("/login")
    }
  }, [hasAuth, status, router])

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

  return (
    <DashboardLayout
      pageTitle="Resources & Career Toolkit"
      pageDescription="Explore curated, high-quality resources to strengthen your resume, boost your career prep, and level up your AI & software skills."
    >
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        {/* Header */}
        <div className="text-center space-y-3 animate-in fade-in slide-in-from-bottom-2">
          <h1 className="text-3xl font-bold text-gray-900">Resources &amp; Career Toolkit</h1>
          <p className="text-gray-600">
            Explore curated, high-quality resources to strengthen your resume, boost your career prep, and level up your AI &amp; software skills.
          </p>
          <div className="h-px bg-gradient-to-r from-blue-200 via-blue-100 to-blue-300 mt-4" />
        </div>

        {/* Resume Building */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Resume Building</h2>
          <p className="text-sm text-gray-600">
            Create professional, ATS-optimized resumes with these trusted platforms.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* FlowCV */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">FlowCV</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Free modern resume builder with clean ATS-optimized templates and instant feedback.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://flowcv.com" target="_blank" rel="noopener noreferrer">
                    Visit <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* Kickresume */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">Kickresume</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                AI-assisted resume builder trusted by professionals at Google, Tesla, and IBM.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://kickresume.com" target="_blank" rel="noopener noreferrer">
                    Visit <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* Overleaf */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">Overleaf CV Templates</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Academic and research-focused CV templates for LaTeX users.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://www.overleaf.com/gallery/tagged/cv" target="_blank" rel="noopener noreferrer">
                    Visit <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
          </div>
        </section>

        {/* Career Guidance */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Career Guidance</h2>
          <p className="text-sm text-gray-600">
            Plan your career growth, explore opportunities, and learn from professionals in the tech industry.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* LinkedIn Career Explorer */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Rocket className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">LinkedIn Career Explorer</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Discover alternate career paths and key skill transitions using your existing experience.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://linkedin.github.io/career-explorer/" target="_blank" rel="noopener noreferrer">
                    Explore <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* FAANGPath */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Rocket className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">FAANGPath</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Get resume reviews, mock interviews, and mentorship from engineers at top tech companies.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://www.faangpath.com/" target="_blank" rel="noopener noreferrer">
                    Explore <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* Levels.fyi */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Rocket className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">Levels.fyi</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Compare salaries, job levels, and compensation packages across companies.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://www.levels.fyi/" target="_blank" rel="noopener noreferrer">
                    Explore <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
          </div>
        </section>

        {/* Skill Development */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Skill Development</h2>
          <p className="text-sm text-gray-600">
            Master the skills needed for AI, ML, and scalable software engineering.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* DeepLearning.AI Short Courses */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Brain className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">DeepLearning.AI Short Courses</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Learn GenAI, LangChain, and LLM fundamentals from Andrew Ng’s official platform.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://www.deeplearning.ai/short-courses/" target="_blank" rel="noopener noreferrer">
                    Start Learning <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* LangChain Academy */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Brain className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">LangChain Academy</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Hands-on courses for building AI agents, RAG systems, and GenAI apps.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://academy.langchain.com/" target="_blank" rel="noopener noreferrer">
                    Start Learning <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
            {/* System Design Primer */}
            <Card className="transition-all border border-gray-200 hover:border-transparent hover:bg-gradient-to-r from-blue-50 to-blue-100 shadow-md hover:shadow-lg hover:scale-[1.02]">
              <CardHeader className="flex items-center gap-3">
                <Brain className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold">System Design Primer (GitHub)</h3>
              </CardHeader>
              <CardContent className="text-gray-600">
                Open-source guide for mastering large-scale system design concepts.
              </CardContent>
              <div className="px-6 pb-6">
                <Button asChild variant="outline" className="w-full">
                  <a href="https://github.com/donnemartin/system-design-primer" target="_blank" rel="noopener noreferrer">
                    Start Learning <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Card>
          </div>
        </section>

        {/* CTA removed per request */}
      </div>
    </DashboardLayout>
  )
}
