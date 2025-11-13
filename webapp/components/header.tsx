"use client"

import Link from "next/link"
import { useSession, signOut } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { usePathname } from "next/navigation"

export function Header() {
  const { status } = useSession()
  const pathname = usePathname()
  const isAuthenticated = status === "authenticated"

  // Don't show header on dashboard pages (they use DashboardLayout)
  const isDashboardPage = pathname?.startsWith("/dashboard") || 
                          pathname?.startsWith("/analyzer") ||
                          pathname?.startsWith("/enhancer") ||
                          pathname?.startsWith("/interview") ||
                          pathname?.startsWith("/analytics") ||
                          pathname?.startsWith("/resources") ||
                          pathname?.startsWith("/profile")

  if (isDashboardPage) {
    return null
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 bg-clip-text text-transparent">
            ResuMate
          </span>
        </Link>
        
        <div className="flex items-center space-x-4">
          {status === "loading" ? (
            <div className="h-8 w-24 rounded-full bg-gray-200 dark:bg-gray-800 animate-pulse" />
          ) : isAuthenticated ? (
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="outline" size="sm">
                  Dashboard
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={() => {
                if (typeof window !== "undefined") {
                  localStorage.removeItem("token")
                }
                signOut({ callbackUrl: "/" })
              }}>
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/signup">
                <Button variant="gradient" size="sm" className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700">
                  Sign Up
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

