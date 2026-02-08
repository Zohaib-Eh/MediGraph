"use client"
import ReactMarkdown from 'react-markdown'
import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Lightbulb, MapPin, Users, Calendar, TrendingUp, Sparkles, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

interface PlanningScenario {
  id: string
  title: string
  description: string
  icon: any
  prompt: string
}

const PLANNING_SCENARIOS: PlanningScenario[] = [
  {
    id: "equipment-gap",
    title: "Equipment Gap Analysis",
    description: "Identify missing critical equipment in a region",
    icon: TrendingUp,
    prompt: "Which facilities lack ultrasound equipment and where should we prioritize distribution?"
  },
  {
    id: "service-expansion",
    title: "Service Expansion Planning",
    description: "Plan new specialty services based on regional needs",
    icon: MapPin,
    prompt: "Which regions need more cardiology services and which facilities could offer them?"
  },
  {
    id: "resource-allocation",
    title: "Resource Allocation",
    description: "Optimize resource distribution across facilities",
    icon: Users,
    prompt: "How should we distribute 10 new ultrasound machines across facilities for maximum impact?"
  },
  {
    id: "capacity-planning",
    title: "Capacity Planning",
    description: "Plan for population growth and demand",
    icon: Calendar,
    prompt: "Which facilities are at capacity and need expansion based on their current utilization?"
  },
]

export function PlanningAssistant() {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [customQuery, setCustomQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleScenarioSelect = async (scenario: PlanningScenario) => {
    setSelectedScenario(scenario.id)
    setCustomQuery(scenario.prompt)
    await executeQuery(scenario.prompt)
  }

  const executeQuery = async (query: string) => {
    if (!query.trim()) return
    
    setIsLoading(true)
    setResult(null)
    
    try {
      const response = await api.query(query, false)
      setResult(response.answer)
    } catch (error) {
      console.error("Planning query error:", error)
      setResult("❌ Error: Could not generate planning recommendation. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCustomQuery = () => {
    executeQuery(customQuery)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="bg-purple-500/10 p-3 rounded-lg">
          <Lightbulb className="h-6 w-6 text-purple-500" />
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-bold">Healthcare Planning Assistant</h2>
          <p className="text-muted-foreground mt-1">
            Get AI-powered recommendations for resource allocation, service expansion, and capacity planning
          </p>
        </div>
      </div>

      {/* Quick Planning Scenarios */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Quick Planning Scenarios</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {PLANNING_SCENARIOS.map((scenario) => {
            const Icon = scenario.icon
            const isSelected = selectedScenario === scenario.id
            
            return (
              <Card
                key={scenario.id}
                className={`cursor-pointer transition-all hover:border-purple-500 hover:shadow-md ${
                  isSelected ? "border-purple-500 bg-purple-500/5" : ""
                }`}
                onClick={() => handleScenarioSelect(scenario)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${isSelected ? "bg-purple-500 text-white" : "bg-muted"}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-sm font-medium">{scenario.title}</CardTitle>
                      <CardDescription className="text-xs mt-1">
                        {scenario.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Custom Query */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            Custom Planning Query
          </CardTitle>
          <CardDescription>
            Ask any planning or strategic question about healthcare resources
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="e.g., Which facilities should receive MRI machines based on patient load and current capabilities?"
            className="min-h-[80px]"
          />
          <Button 
            onClick={handleCustomQuery} 
            disabled={isLoading || !customQuery.trim()}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Recommendation
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card className="border-purple-500/50 bg-purple-500/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-purple-500" />
              <CardTitle className="text-base">Planning Recommendation</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>
                {result}
              </ReactMarkdown>
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <Badge variant="outline" className="text-xs">
                <Sparkles className="h-3 w-3 mr-1" />
                AI-Generated Recommendation
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                This recommendation is based on current data in the knowledge graph. 
                Always verify with domain experts before implementing strategic decisions.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Help Text */}
      {!result && !isLoading && (
        <Card className="bg-muted/30">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Lightbulb className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="text-sm text-muted-foreground space-y-2">
                <p className="font-medium text-foreground">How to use the Planning Assistant:</p>
                <ul className="space-y-1 ml-4 list-disc">
                  <li>Click a quick scenario card for instant analysis</li>
                  <li>Or write your own custom planning question</li>
                  <li>Get AI-powered recommendations based on your knowledge graph data</li>
                  <li>Use insights to make data-driven strategic decisions</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
