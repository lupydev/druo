Disclaimer
The sole purpose of this document is to perform a general validation of the skills associated with
the role you are applying for. This document does not represent an acceptance, hiring,
commitment, or obligation to provide services for DRUO Inc. The company used in this
document is fictitious, and any similarity to a real company is unintentional.

THE CHALLENGE

1.  Think strategically about a product problem (PRD)
2.  Execute rapidly and deliver a working prototype (AI tools welcome but not required)
    This test mirrors the real job at Novo: Balance planning with building, move fast, ship working
    solutions.

CASE STUDY: Retry Logic for Failed Payments
Background
Novo processes payments for merchants across LATAM. Currently, when a payment fails
(insufficient funds, card declined, network timeout), the system marks it as "failed" and the merchant
must manually retry.
The Problem:
● ~15% of transactions fail on first attempt
● ~40% of failures could succeed if retried automatically
● Manual retries create friction for merchants and customers
● Lost revenue: Potential +$500K USD/month in GMV if fixed
Your Mission: Design and build an MVP for automatic payment retry logic.

Stakeholder Context (Quick Version)
CFO: Wants to maximize payment conversion. Needs ROI and timeline.
CTO/Engineering: Worried about system complexity, rate limits, API costs. Needs clear specs.
Risk/Compliance: Must comply with PCI-DSS. Cannot retry indefinitely. Needs audit trail.
Merchants: Want control over retry behavior. Need visibility into retry attempts.

Technical Context
Current Stack:
● Backend: Node.js microservices
● Database: PostgreSQL + BigQuery
● Payment Processors: Stripe, PSE, Nequi (each has different retry policies)
Known Constraints:
● Payment processors have rate limits (e.g., Stripe max 5 retries per card per 24h)
● Some failures should NOT be retried (e.g., "card stolen")
● Retry attempts cost money (processor fees)
● Timeline: MVP in 6 weeks, 2 backend engineers @ 50% time

Failure Types (Data)
Failure Type % of Failures Should Retry? Success Rate on Retry
Insufficient funds 35% Yes, after delay 20%
Card declined (generic) 25% Yes, limited 15%
Network timeout 20% Yes, immediate 60%
Processor downtime 5% Yes, after delay 80%

YOUR DELIVERABLES
You must submit TWO components:
Part 1: PRD
Section 1: Problem & MVP Scope
Define:
● Problem Statement: What are we solving and why now?
● Assumptions: What are you assuming about user behavior, tech, market?
● MVP Scope: What's IN vs. OUT and why?
○ Use a simple table or list format
○ Be specific: "Must-have: X, Y, Z" / "Nice-to-have: A, B" / "Out of scope: C"
● Key Risks: Top risks (technical, business, regulatory) and how you'd mitigate
Section 2: Execution Plan
Define:
● Backlog: Break MVP into epics or features
○ For each: brief description, priority (P0/P1/P2), estimated effort (S/M/L)
○ Show dependencies if any
● Success Metrics: Define key metrics
○ At least 1 leading indicator (measurable during development)
○ At least 1 lagging indicator (business outcome)
○ How will you measure them? (what events to track, what queries to run)
● Rollout Plan: How will you launch this?
○ Beta with X merchants → gradual rollout → 100%
○ Timeline (e.g., "Week 6: Beta, Week 8: 30%, Week 10: 100%")
● Add a diagram explaining the components and technologies used in the solution.
What we're evaluating:
● Do you understand the problem deeply?
● Is your MVP scope realistic for 6 weeks / 1 FTE?
● Can you prioritize effectively?
● Are your metrics actionable?
● Do you balance all stakeholders (CFO, CTO, Risk, Merchants)?

Part 2: Working Prototype
Merchant Retry Configuration Dashboard
Build a simple web interface where merchants can:
● View current retry settings (max attempts, retry intervals)
● Configure retry rules (toggle retry on/off for different failure types)
● See a preview/simulation (e.g., "With these settings, ~X% of failures would be retried")
Tech suggestions: v0.dev, Bolt.new, Cursor + React, Replit, etc
Scope:
● 1-2 screens  
● Basic form inputs (dropdowns, toggles, sliders)
● Mock data is fine (real backend is a plus)
● Focus: UX makes sense, settings are configurable

Build an automated workflow that:
● Detects a failed payment (webhook or manual trigger)
● Applies retry logic based on failure type
● Schedules retry attempts (e.g., immediate, then 1h later, then 24h later)
● Logs all attempts
● Sends notification on final success/failure
Tech suggestions: n8n, Make.com, Zapier, etc
Scope:
● Working workflow deployed  
● Can trigger it manually and see it run
● Focus: Logic is correct, workflow is automated
● Data model, tables created and relationships, uses preferred database engine.

Connect dashboard with automated workflow.

Implementation Requirements (ALL options)
Must include:
● Working demo (deployed link OR video showing it works)
● README with:
○ What you built and why you chose this option
○ How to run/test it (clear setup instructions)
○ Tools/approach used (if you used AI tools, document which ones and how they
helped)
○ What you'd improve with more time
● Clean code/workflow (readable, organized)
