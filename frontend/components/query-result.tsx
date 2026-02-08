"use client"

import { useState } from "react"
import {
  MessageSquare,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Copy,
  Check,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type { QueryResult } from "@/lib/api"
import ReactMarkdown from 'react-markdown'

interface QueryResultProps {
  query: string
  result: QueryResult
}

export function QueryResultCard({ query, result }: QueryResultProps) {
  const [showTrace, setShowTrace] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(result.answer)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <MessageSquare className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Your query</p>
              <p className="text-base font-semibold text-foreground">{query}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? (
              <Check className="h-3.5 w-3.5 text-[hsl(var(--success))]" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="prose prose-sm max-w-none rounded-lg bg-muted/50 p-4">
          <ReactMarkdown>
            {result.answer}
          </ReactMarkdown>
        </div>

        {result.citations && result.citations.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
              <p className="text-xs font-medium text-muted-foreground">Citations</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.citations.map((citation, i) => (
                <Badge key={i} variant="secondary" className="text-xs font-normal">
                  {citation.source}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {result.trace && (
          <div className="border-t pt-3">
            <button
              type="button"
              onClick={() => setShowTrace(!showTrace)}
              className="flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {showTrace ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
              Technical Details
            </button>
            {showTrace && (
              <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-secondary p-3 font-mono text-xs text-secondary-foreground">
                {JSON.stringify(result.trace, null, 2)}
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
