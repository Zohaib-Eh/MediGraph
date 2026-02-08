"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
  Activity,
  Upload,
  Network,
  Search,
  Lightbulb,
  ArrowRight,
  Sparkles,
} from "lucide-react"
import { Button } from "@/components/ui/button"

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
}

const stagger = {
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
}

const features = [
  {
    icon: Upload,
    title: "Upload & Parse",
    description:
      "Drop CSV files and let AI extract facilities, equipment, specialties, and relationships automatically.",
  },
  {
    icon: Network,
    title: "Knowledge Graph",
    description:
      "Build a Neo4j-powered graph of your healthcare data. Visualize entities and connections at a glance.",
  },
  {
    icon: Search,
    title: "AI-Powered Query",
    description:
      "Ask questions in plain language. Get answers backed by your knowledge graph with source citations.",
  },
  {
    icon: Lightbulb,
    title: "Planning Assistant",
    description:
      "Get recommendations for resource allocation, capacity planning, and service expansion.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Nav */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl"
      >
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
              <Activity className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-foreground">
              MediGraph
            </span>
          </Link>
          <Link href="/app">
            <Button
              size="sm"
              className="rounded-lg bg-primary px-4 font-medium text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90"
            >
              Enter App
              <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </motion.nav>

      {/* Hero */}
      <section className="relative flex flex-1 flex-col items-center justify-center px-4 py-24 lg:py-32">
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute left-1/2 top-0 h-[60vh] w-[80vw] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="mx-auto max-w-4xl text-center"
        >
          <motion.div
            variants={fadeUp}
            className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1.5 text-xs font-medium text-primary"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Intelligent Document Parser
          </motion.div>
          <motion.h1
            variants={fadeUp}
            className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl lg:leading-[1.1]"
          >
            Turn healthcare data into a{" "}
            <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              living knowledge graph
            </span>
          </motion.h1>
          <motion.p
            variants={fadeUp}
            className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl"
          >
            Upload CSV, extract entities with AI, and query facilities, equipment,
            and specialties in plain language. Built for planners and analysts.
          </motion.p>
          <motion.div
            variants={fadeUp}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <Link href="/app">
              <Button
                size="lg"
                className="h-12 rounded-xl bg-primary px-8 text-base font-semibold shadow-lg shadow-primary/25 hover:bg-primary/90"
              >
                Get started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/app?tab=query">
              <Button
                size="lg"
                variant="outline"
                className="h-12 rounded-xl border-border bg-transparent px-8 text-base font-medium hover:bg-muted/50"
              >
                Try a query
              </Button>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="border-t border-border/50 bg-card/30 py-24 lg:py-32">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Everything you need in one place
            </h2>
            <p className="mt-3 text-muted-foreground">
              From raw CSV to actionable insights with AI and graph technology.
            </p>
          </motion.div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                whileHover={{ y: -4 }}
                className="group rounded-2xl border border-border/50 bg-card/80 p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary transition-colors group-hover:bg-primary/25">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold tracking-tight text-foreground">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 lg:py-32">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl rounded-3xl border border-border/50 bg-gradient-to-b from-card to-card/50 px-8 py-16 text-center shadow-xl"
        >
          <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Ready to explore your data?
          </h2>
          <p className="mt-3 text-muted-foreground">
            Upload a CSV, build your graph, and start querying in minutes.
          </p>
          <Link href="/app" className="mt-8 inline-block">
            <Button
              size="lg"
              className="h-12 rounded-xl bg-primary px-8 text-base font-semibold shadow-lg shadow-primary/25 hover:bg-primary/90"
            >
              Open MediGraph
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8">
        <div className="mx-auto max-w-6xl px-4 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20">
              <Activity className="h-4 w-4 text-primary" />
            </div>
            <span className="font-semibold text-foreground">MediGraph</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Intelligent Document Parser & Medical Knowledge Graph
          </p>
          <Link
            href="/app"
            className="text-sm font-medium text-primary hover:underline"
          >
            Enter app →
          </Link>
        </div>
      </footer>
    </div>
  )
}
