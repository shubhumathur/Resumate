"use client"

import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, CheckCircle, Zap, BarChart3, Target, Sparkles } from "lucide-react"

export default function Home() {
  const { status } = useSession()
  const router = useRouter()

  // Redirect authenticated users to dashboard when session resolves
  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard")
    }
  }, [status, router])

  if (status === "loading") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center space-y-4 text-center text-muted-foreground animate-in fade-in">
          <div className="h-12 w-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm font-medium">Getting things ready...</p>
        </div>
      </div>
    )
  }

  if (status === "authenticated") {
    return null
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="container py-24 md:py-32">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl md:text-7xl bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 bg-clip-text text-transparent">
              Your AI Career Assistant for Smarter Resume Matching
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              ResuMate uses AI to analyze your resume against job descriptions, 
              providing detailed insights and recommendations to help you land your dream job.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/analyzer">
                <Button size="lg" className="text-lg px-8 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white">
                  Try Demo
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="text-lg px-8 border-gray-300 dark:border-gray-600">
                  Login to Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container py-24 border-t border-gray-200 dark:border-gray-700">
          <div className="mx-auto max-w-6xl">
            <h2 className="text-3xl font-bold text-center mb-12 text-gray-900 dark:text-gray-100">Why Choose ResuMate?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <Zap className="h-12 w-12 text-blue-600 dark:text-blue-400 mb-4" />
                  <CardTitle className="text-gray-900 dark:text-gray-100">Instant Analysis</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Get your resume matched with job descriptions in seconds using advanced AI.
                  </CardDescription>
                </CardHeader>
              </Card>
              
              <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <BarChart3 className="h-12 w-12 text-blue-600 dark:text-blue-400 mb-4" />
                  <CardTitle className="text-gray-900 dark:text-gray-100">Detailed Insights</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Receive comprehensive scores for skills, experience, and semantic similarity.
                  </CardDescription>
                </CardHeader>
              </Card>
              
              <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <Target className="h-12 w-12 text-green-600 dark:text-green-400 mb-4" />
                  <CardTitle className="text-gray-900 dark:text-gray-100">Actionable Recommendations</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Get personalized suggestions to improve your resume and interview prep questions.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </section>

        {/* Sample Visualization Section */}
        <section className="container py-24 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="mx-auto max-w-4xl">
            <h2 className="text-3xl font-bold text-center mb-12 text-gray-900 dark:text-gray-100">See How It Works</h2>
            <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-lg">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-gray-100">Sample Match Analysis</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Here&apos;s what a typical analysis looks like
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    <span className="font-medium text-gray-900 dark:text-gray-100">Suitability Score</span>
                    <span className="text-2xl font-bold bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 bg-clip-text text-transparent">85%</span>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Skill Overlap</div>
                      <div className="text-xl font-bold mt-2 text-gray-900 dark:text-gray-100">90%</div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Experience</div>
                      <div className="text-xl font-bold mt-2 text-gray-900 dark:text-gray-100">80%</div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Semantic</div>
                      <div className="text-xl font-bold mt-2 text-gray-900 dark:text-gray-100">85%</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container py-24 border-t border-gray-200 dark:border-gray-700">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-gray-100">Ready to Get Started?</h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              Join thousands of job seekers who are improving their resumes with AI.
            </p>
            <Link href="/signup">
              <Button size="lg" className="text-lg px-8 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}
