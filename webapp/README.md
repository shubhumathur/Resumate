# ResuMate Web App

The frontend web application for ResuMate, built with Next.js, TypeScript, TailwindCSS, and shadcn/ui.

## Features

- 🎨 Modern, gradient-based UI with dark mode support
- 🔐 Authentication with NextAuth.js (Google, GitHub, Credentials)
- 📊 Resume-JD Analyzer with detailed match scores
- 💼 Dashboard with analysis history
- 📈 Analytics and insights
- 🚀 Resume Enhancer
- 💡 Job Recommendations
- 🎯 Interview Prep with AI-generated questions

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- MongoDB (running locally or cloud instance)
- FastAPI backend running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp env.example .env.local
```

3. Configure your `.env.local` file with:
   - NextAuth secret (generate one: `openssl rand -base64 32`)
   - OAuth provider credentials (Google, GitHub)
   - FastAPI backend URL
   - MongoDB connection string

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

See `env.example` for all required environment variables.

Key variables:
- `NEXTAUTH_SECRET`: Secret for NextAuth.js sessions
- `NEXTAUTH_URL`: Your app URL (http://localhost:3000 for development)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Google OAuth credentials
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: GitHub OAuth credentials
- `NEXT_PUBLIC_FASTAPI_BASE_URL`: Backend API URL (default: http://localhost:8000)

## Project Structure

```
webapp/
├── app/                    # Next.js App Router pages
│   ├── api/               # API routes (NextAuth)
│   ├── analyzer/          # Resume-JD Analyzer page
│   ├── dashboard/         # User dashboard
│   ├── enhancer/          # Resume enhancer
│   ├── analytics/         # Analytics page
│   └── ...
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── header.tsx        # Header component
│   └── footer.tsx        # Footer component
├── lib/                   # Utilities and API client
│   ├── api.ts            # FastAPI client
│   ├── utils.ts          # Utility functions
│   └── types.ts          # TypeScript types
└── types/                 # Type definitions
```

## Building for Production

```bash
npm run build
npm start
```

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **shadcn/ui** - UI components
- **NextAuth.js** - Authentication
- **Recharts** - Data visualization
- **Axios** - HTTP client

## License

MIT

