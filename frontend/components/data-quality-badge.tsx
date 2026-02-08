"use client"

import { CheckCircle2, AlertCircle, XCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface DataQualityBadgeProps {
  completeness: number // 0-100 percentage
  className?: string
}

export function DataQualityBadge({ completeness, className }: DataQualityBadgeProps) {
  const getQualityInfo = () => {
    if (completeness >= 80) {
      return {
        label: "Excellent",
        variant: "default" as const,
        icon: CheckCircle2,
        color: "text-green-600 dark:text-green-400",
        bg: "bg-green-50 dark:bg-green-950",
      }
    } else if (completeness >= 60) {
      return {
        label: "Good",
        variant: "secondary" as const,
        icon: CheckCircle2,
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-50 dark:bg-blue-950",
      }
    } else if (completeness >= 40) {
      return {
        label: "Fair",
        variant: "secondary" as const,
        icon: AlertCircle,
        color: "text-yellow-600 dark:text-yellow-400",
        bg: "bg-yellow-50 dark:bg-yellow-950",
      }
    } else {
      return {
        label: "Poor",
        variant: "destructive" as const,
        icon: XCircle,
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-50 dark:bg-red-950",
      }
    }
  }

  const quality = getQualityInfo()
  const Icon = quality.icon

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant={quality.variant} className={`gap-1.5 ${quality.bg} ${className}`}>
            <Icon className={`h-3 w-3 ${quality.color}`} />
            <span>{quality.label}</span>
            <span className="text-xs opacity-70">{Math.round(completeness)}%</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">
            Data completeness: {Math.round(completeness)}%
            <br />
            {completeness >= 80 && "All critical fields populated"}
            {completeness >= 60 && completeness < 80 && "Most fields populated"}
            {completeness >= 40 && completeness < 60 && "Some fields missing"}
            {completeness < 40 && "Many fields missing"}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
