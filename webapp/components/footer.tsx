"use client"

import Link from "next/link"
import { useSession } from "next-auth/react"
import { useEffect, useState } from "react"

export function Footer() {
  const { data: session } = useSession()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const token = mounted && typeof window !== "undefined" ? localStorage.getItem("token") : null
  const isAuthenticated = session || token

  return (
    <footer className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="container py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">ResuMate</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI-powered resume matching platform to help you find the perfect job fit.
            </p>
          </div>
          
          {isAuthenticated && (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Product</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>
                  <Link href="/analyzer" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    Resume Analyzer
                  </Link>
                </li>
                <li>
                  <Link href="/enhancer" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    Resume Enhancer
                  </Link>
                </li>
                <li>
                  <Link href="/interview" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    Interview Prep
                  </Link>
                </li>
              </ul>
            </div>
          )}
          
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Resources</h4>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              {isAuthenticated ? (
                <>
                  <li>
                    <Link href="/resources" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      How to Improve ATS Score
                    </Link>
                  </li>
                  <li>
                    <Link href="/resources" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      Resume Optimization Tips
                    </Link>
                  </li>
                </>
              ) : null}
              <li>
                <Link href="/contact" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
          
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li>
                <Link href="/privacy" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>© {new Date().getFullYear()} ResuMate. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

