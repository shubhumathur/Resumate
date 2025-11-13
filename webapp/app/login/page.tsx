"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useSession } from "next-auth/react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { authApi } from "@/lib/api"
import { Github, Mail, Linkedin, CheckCircle, Loader2 } from "lucide-react"

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session } = useSession()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [signupSuccess, setSignupSuccess] = useState(false)

  // Check if user is already authenticated
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    if (session || token) {
      router.push("/dashboard")
    }
  }, [session, router])

  // Check for signup success message
  useEffect(() => {
    if (searchParams.get("signup") === "success") {
      setSignupSuccess(true)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSignupSuccess(false)

    try {
      const response = await authApi.login(email, password)
      console.log("Login response:", response)
      
      if (response && response.success && response.token) {
        // Store token
        localStorage.setItem("token", response.token)
        console.log("✅ Login successful! Token stored.")
        console.log("🔄 Redirecting to dashboard...")
        
        // Use window.location.replace for immediate redirect without history entry
        window.location.replace("/dashboard")
      } else {
        setError(response?.detail || "Invalid email or password")
      }
    } catch (loginErr: any) {
      console.error("❌ Login error:", loginErr)
      
      // Extract error message
      let errorMessage = "Invalid email or password"
      if (loginErr?.response?.data?.detail) {
        errorMessage = loginErr.response.data.detail
      } else if (loginErr?.response?.data?.message) {
        errorMessage = loginErr.response.data.message
      } else if (loginErr?.message) {
        errorMessage = loginErr.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleOAuth = async (provider: string) => {
    setLoading(true)
    window.location.href = `/api/auth/signin/${provider}?callbackUrl=/dashboard`
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="flex-1 flex items-center justify-center container py-12">
        <Card className="w-full max-w-md bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">
              Welcome back
            </CardTitle>
            <CardDescription className="text-center text-gray-500 dark:text-gray-400">
              Sign in to your account to continue
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {signupSuccess && (
              <div className="text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-3 rounded-md border border-green-200 dark:border-green-800 flex items-center space-x-2">
                <CheckCircle className="h-4 w-4" />
                <span>Account created successfully! Please sign in.</span>
              </div>
            )}

            <div className="grid grid-cols-3 gap-4">
              <Button
                variant="outline"
                type="button"
                onClick={() => handleOAuth("google")}
                disabled={loading}
                className="w-full"
              >
                <Mail className="mr-2 h-4 w-4" />
                Google
              </Button>
              <Button
                variant="outline"
                type="button"
                onClick={() => handleOAuth("github")}
                disabled={loading}
                className="w-full"
              >
                <Github className="mr-2 h-4 w-4" />
                GitHub
              </Button>
              <Button
                variant="outline"
                type="button"
                onClick={() => handleOAuth("linkedin")}
                disabled={loading}
                className="w-full"
              >
                <Linkedin className="mr-2 h-4 w-4" />
                LinkedIn
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-gray-200 dark:border-gray-700" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white dark:bg-gray-800 px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-gray-900 dark:text-gray-100">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="text-gray-900 dark:text-gray-100">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                />
              </div>

              {error && (
                <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-md border border-red-200 dark:border-red-800">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                variant="gradient"
                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </form>

            <div className="text-center text-sm text-gray-600 dark:text-gray-400">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="text-blue-600 dark:text-blue-400 hover:underline font-medium">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
      
      <Footer />
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-900">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </main>
        <Footer />
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}

