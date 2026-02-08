"use client"

import React from "react"
import { useCallback, useState, useRef } from "react"
import { motion } from "framer-motion"
import { Upload, FileText, CheckCircle2, AlertCircle, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import type { UploadResult } from "@/lib/api"

interface FileUploadProps {
  onUploadComplete: (result: UploadResult) => void
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const validateFile = (f: File): boolean => {
    if (!f.name.endsWith(".csv")) {
      setError("Only CSV files are accepted")
      return false
    }
    if (f.size > 50 * 1024 * 1024) {
      setError("File size must be less than 50MB")
      return false
    }
    return true
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    setError(null)
    setResult(null)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setResult(null)
    const selectedFile = e.target.files?.[0]
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    setProgress(0)

    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 15, 90))
    }, 300)

    try {
      const uploadResult = await api.upload(file)
      clearInterval(interval)
      setProgress(100)
      setResult(uploadResult)
      onUploadComplete(uploadResult)
    } catch (err) {
      clearInterval(interval)
      setError(err instanceof Error ? err.message : "Upload failed")
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setProgress(0)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  return (
    <Card className="overflow-hidden border-border/50 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold tracking-tight">Upload Data</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {!result ? (
          <>
            <motion.div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click()
              }}
              role="button"
              tabIndex={0}
              whileHover={{ scale: 1.005 }}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors",
                isDragging
                  ? "border-primary bg-primary/10"
                  : "border-border hover:border-primary/50 hover:bg-muted/50",
                error && "border-destructive/50"
              )}
            >
              <motion.div
                animate={isDragging ? { scale: [1, 1.08, 1] } : {}}
                transition={{ repeat: isDragging ? Infinity : 0, duration: 1.2 }}
                className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted"
              >
                <Upload className="h-6 w-6 text-muted-foreground" />
              </motion.div>
              <div className="text-center">
                <p className="text-sm font-medium text-foreground">
                  Drop CSV file here or click to browse
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  CSV format only, max 50MB
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
            </motion.div>

            {file && (
              <div className="flex items-center gap-3 rounded-lg border bg-muted/30 p-3">
                <FileText className="h-5 w-5 text-primary" />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={handleReset} aria-label="Remove file">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {uploading && (
              <div className="flex flex-col gap-2">
                <Progress value={progress} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  Uploading and processing... {progress}%
                </p>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <Button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full"
            >
              <Upload className="mr-2 h-4 w-4" />
              {uploading ? "Uploading..." : "Upload CSV"}
            </Button>
          </>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col gap-4"
          >
            <div className="flex items-center gap-2 rounded-xl border border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 p-3">
              <CheckCircle2 className="h-5 w-5 text-[hsl(var(--success))]" />
              <div>
                <p className="text-sm font-medium text-foreground">Upload Successful</p>
                <p className="text-xs text-muted-foreground">{result.message}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border bg-muted/30 p-3 text-center">
                <p className="text-xl font-bold text-foreground">{result.total_entities}</p>
                <p className="text-xs text-muted-foreground">Total Entities</p>
              </div>
              {result.breakdown &&
                Object.entries(result.breakdown).slice(0, 3).map(([type, count]) => (
                  <div key={type} className="rounded-lg border bg-muted/30 p-3 text-center">
                    <p className="text-xl font-bold text-foreground">{count}</p>
                    <p className="text-xs capitalize text-muted-foreground">{type}</p>
                  </div>
                ))}
            </div>

            {result.sample_facilities && result.sample_facilities.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-sm font-medium text-foreground">Sample Facilities</p>
                {result.sample_facilities.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 rounded-md border bg-card p-2">
                    <Badge variant="secondary" className="text-xs">
                      {f.type}
                    </Badge>
                    <span className="text-sm text-foreground">{f.name}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{f.location}</span>
                  </div>
                ))}
              </div>
            )}

            <Button variant="outline" onClick={handleReset}>
              Upload Another File
            </Button>
          </motion.div>
        )}
      </CardContent>
    </Card>
  )
}
