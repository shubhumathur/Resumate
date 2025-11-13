import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import GitHubProvider from "next-auth/providers/github"
import CredentialsProvider from "next-auth/providers/credentials"
import { authApi } from "@/lib/api"

const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID || "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }
        try {
          const response = await authApi.login(credentials.email, credentials.password)
          if (response.success && response.user) {
            return {
              id: response.user._id,
              email: response.user.email,
              name: response.user.name,
            }
          }
          return null
        } catch (error) {
          return null
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    async jwt({ token, user, account }: any) {
      if (user) {
        token.id = user.id
      }
      if (account?.provider === "credentials" && user) {
        // Store token from credentials login
        try {
          const tokenResponse = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || "http://localhost:8000"}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: user.email,
              password: "", // Not needed for OAuth
            }),
          })
          if (tokenResponse.ok) {
            const data = await tokenResponse.json()
            token.accessToken = data.token
          }
        } catch (err) {
          // Ignore errors
        }
      }
      return token
    },
    async session({ session, token }: any) {
      if (session.user) {
        session.user.id = token.id as string
      }
      return session
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
}

const handler = NextAuth(authOptions as any)

export { handler as GET, handler as POST }
