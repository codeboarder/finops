from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import aiosqlite
import random
import asyncio
from datetime import datetime, timedelta
import json
import httpx
import os

# Azure service imports - Phase 1
try:
    from app.services.cost_service import CostService
    from app.services.recommendation_service import RecommendationService
    from app.services.budget_service import BudgetService
    AZURE_SERVICES_AVAILABLE = True
except ImportError:
    AZURE_SERVICES_AVAILABLE = False
    print("Azure services not available - running in demo mode")

# Phase 2 imports
try:
    from app.database import init_history_db, get_db
    from app.scheduler import start_scheduler, stop_scheduler, get_scheduler
    from app.models.cost_history import DailyCostHistory, AnomalyRecord, BudgetStatus
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False
    print("Phase 2 features not available")

# GPT-5 API Configuration (Azure OpenAI)
# Set these environment variables for GPT-5 integration:
# GPT5_ENDPOINT - Azure OpenAI endpoint URL
# GPT5_API_KEY - Azure OpenAI API key
GPT5_ENDPOINT = os.getenv("GPT5_ENDPOINT", "https://pharma-agents-jnj-resource.cognitiveservices.azure.com/openai/deployments/gpt-5/chat/completions?api-version=2025-01-01-preview")
GPT5_API_KEY = os.getenv("GPT5_API_KEY", "")

async def call_gpt5_api(user_message: str, context: str = "") -> str:
    """Call GPT-5 via Azure OpenAI"""
    headers = {
        "Content-Type": "application/json",
        "api-key": GPT5_API_KEY,
    }
    
    system_prompt = f"""You are Azure FinOps Copilot for AdventHealth. You help analyze Azure costs, anomalies, and provide RI/SP recommendations.

Current Context:
{context}

Respond concisely and professionally. Use bullet points for lists. Include specific numbers when available."""

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_completion_tokens": 800,
        "stream": False,
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(GPT5_ENDPOINT, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"GPT-5 API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"GPT-5 API error: {str(e)}")
            return None

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

DATABASE = "finops.db"

class ChatMessage(BaseModel):
    message: str

class AzureConfig(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str

# In-memory storage for Azure config (would be encrypted in production)
azure_config_store = {}

# Initialize database
async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS vms (
                id TEXT PRIMARY KEY,
                name TEXT,
                resource_group TEXT,
                vm_type TEXT,
                os_type TEXT,
                size TEXT,
                region TEXT,
                status TEXT,
                cpu_utilization REAL,
                memory_utilization REAL,
                cost_per_hour REAL,
                monthly_cost REAL,
                stability_score REAL,
                growth_rate REAL,
                recommendation TEXT,
                confidence REAL,
                potential_savings REAL,
                is_runaway INTEGER,
                last_updated TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS vm_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vm_id TEXT,
                timestamp TEXT,
                cpu_utilization REAL,
                memory_utilization REAL,
                cost REAL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                severity TEXT,
                resource TEXT,
                message TEXT,
                delta TEXT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS hidden_costs (
                id TEXT PRIMARY KEY,
                category TEXT,
                name TEXT,
                detected REAL,
                mitigated REAL,
                monthly_savings REAL,
                status TEXT,
                managed_by TEXT,
                progress REAL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id TEXT PRIMARY KEY,
                name TEXT,
                current REAL,
                allocated REAL,
                forecast REAL,
                status TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mission_critical (
                id TEXT PRIMARY KEY,
                name TEXT,
                monthly_cost REAL,
                protection_level TEXT,
                coverage_type TEXT,
                capacity_headroom REAL,
                status TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource TEXT,
                anomaly_type TEXT,
                category TEXT,
                severity TEXT,
                detected_at TEXT,
                cost_impact REAL,
                root_cause TEXT,
                resolution TEXT,
                status TEXT,
                resolved_at TEXT,
                resolved_by TEXT,
                created_by_agent TEXT,
                validation_confidence REAL
            )
        ''')
        
        await db.commit()
        await seed_data(db)

async def seed_data(db):
    # Always refresh ALL data to ensure latest values on every startup
    await db.execute("DELETE FROM budgets")
    await db.execute("DELETE FROM alerts")
    await db.execute("DELETE FROM vms")
    await db.execute("DELETE FROM vm_history")
    await db.execute("DELETE FROM hidden_costs")
    await db.execute("DELETE FROM mission_critical")
    await db.execute("DELETE FROM anomaly_history")
    
    now = datetime.utcnow().isoformat()
    
    # Budget data - Based on AdventHealth December 2025 MBR
    # 4 healthy (green), 1 warning (yellow), 1 critical (red) - showing 98% healthy
    budgets = [
        ("budget-compute", "Compute (ADC VMs)", 172000, 210000, 185000, "critical"),  # 82% - critical (red) - compute overrun
        ("budget-storage", "Storage (1.5PB)", 52000, 103000, 58000, "ok"),  # 50% - healthy (green)
        ("budget-network", "Network & Egress", 17000, 32000, 19000, "ok"),  # 53% - healthy (green)
        ("budget-aiml", "AI/ML & GPU (3P)", 45000, 52000, 48000, "warning"),  # 87% - warning (yellow) - GPU costs growing
        ("budget-database", "Database & SQL", 41000, 75000, 45000, "ok"),  # 55% - healthy (green)
        ("budget-dr", "DR & ASR (ADC DR)", 85000, 159000, 92000, "ok"),  # 53% - healthy (green)
    ]
    
    for b in budgets:
        await db.execute('''
            INSERT OR REPLACE INTO budgets (id, name, current, allocated, forecast, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', b)
    
    # VMs with RHEL, Windows, SQL Always On, ASR - including one runaway
    vms = [
        # RUNAWAY VM - GPU Training gone wild
        ("vm-runaway-gpu", "GPU-Training-Runaway", "rg-ai-workloads", "GPU VMs", "Linux", "Standard_NC24ads_A100_v4", "eastus2", "running",
         98.5, 94.2, 12.50, 9000.0, 45.0, 85.0, "INVESTIGATE", 98.0, 6500.0, 1),
        # SQL Always On Cluster - stable, 3yr RI candidate
        ("vm-sql-prod-01", "SQL-Prod-Primary", "rg-databases", "SQL Server", "Windows", "Standard_E32s_v5", "eastus", "running",
         72.0, 68.0, 2.45, 1764.0, 98.0, 2.0, "3-Year RI", 95.0, 45000.0, 0),
        ("vm-sql-prod-02", "SQL-Prod-Secondary", "rg-databases", "SQL Server", "Windows", "Standard_E32s_v5", "eastus", "running",
         45.0, 52.0, 2.45, 1764.0, 97.0, 2.0, "3-Year RI", 94.0, 44000.0, 0),
        # RHEL VMs - Epic Integration
        ("vm-epic-01", "Epic-Integration-VM1", "rg-epic", "Virtual Machines", "RHEL", "Standard_D16s_v5", "eastus", "running",
         68.0, 72.0, 0.92, 662.4, 96.0, 3.0, "3-Year RI", 93.0, 38000.0, 0),
        ("vm-epic-02", "Epic-Integration-VM2", "rg-epic", "Virtual Machines", "RHEL", "Standard_D16s_v5", "eastus", "running",
         65.0, 70.0, 0.92, 662.4, 95.0, 4.0, "3-Year RI", 92.0, 37000.0, 0),
        # Windows VMs - AKS Production
        ("vm-aks-prod", "AKS-Production", "rg-kubernetes", "Kubernetes", "Linux", "Standard_D16s_v5", "eastus", "running",
         78.0, 72.0, 0.92, 662.4, 78.0, 18.0, "1-Year SP", 88.0, 38000.0, 0),
        # ASR Protected VMs
        ("vm-asr-web-01", "ASR-Web-Primary", "rg-web-dr", "Virtual Machines", "Windows", "Standard_D8s_v5", "eastus", "running",
         55.0, 48.0, 0.46, 331.2, 92.0, 5.0, "1-Year RI", 90.0, 18000.0, 0),
        ("vm-asr-web-02", "ASR-Web-DR", "rg-web-dr", "Virtual Machines", "Windows", "Standard_D8s_v5", "westus2", "running",
         12.0, 15.0, 0.46, 331.2, 94.0, 2.0, "1-Year RI", 89.0, 17000.0, 0),
        # AI Inference Pool - growing workload
        ("vm-ai-inference", "AI-Inference-Pool", "rg-ai-workloads", "GPU VMs", "Linux", "Standard_NC6s_v3", "eastus2", "running",
         82.0, 78.0, 3.50, 2520.0, 65.0, 25.0, "1-Year SP", 82.0, 28000.0, 0),
        # Dev/Test - auto-shutdown candidates
        ("vm-dev-rhel", "Dev-RHEL-Test", "rg-dev", "Virtual Machines", "RHEL", "Standard_D4s_v5", "eastus", "running",
         15.0, 22.0, 0.23, 165.6, 60.0, 5.0, "Auto-Shutdown", 85.0, 8000.0, 0),
        ("vm-dev-win", "Dev-Windows-Test", "rg-dev", "Virtual Machines", "Windows", "Standard_D4s_v5", "eastus", "running",
         18.0, 25.0, 0.23, 165.6, 58.0, 3.0, "Auto-Shutdown", 84.0, 7500.0, 0),
        # Underutilized - rightsize candidates
        ("vm-web-pool-01", "Web-Pool-01", "rg-web", "Virtual Machines", "Windows", "Standard_D8s_v5", "eastus", "running",
         25.0, 32.0, 0.46, 331.2, 75.0, -12.0, "Rightsize", 72.0, 12000.0, 0),
    ]
    
    for vm in vms:
        await db.execute('''
            INSERT INTO vms (id, name, resource_group, vm_type, os_type, size, region, status, cpu_utilization, 
                           memory_utilization, cost_per_hour, monthly_cost, stability_score, 
                           growth_rate, recommendation, confidence, potential_savings, is_runaway, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (*vm, now))
    
    # Generate 90 days of history for each VM
    for vm in vms:
        vm_id = vm[0]
        is_runaway = vm[17]
        base_cpu = vm[8]
        base_mem = vm[9]
        base_cost = vm[10]
        
        for day in range(90):
            timestamp = (datetime.utcnow() - timedelta(days=90-day)).isoformat()
            
            if is_runaway:
                if day < 60:
                    cpu = base_cpu * 0.4 + random.uniform(-5, 5)
                    mem = base_mem * 0.4 + random.uniform(-5, 5)
                    cost = base_cost * 0.3
                elif day < 80:
                    cpu = base_cpu * 0.6 + random.uniform(-3, 10)
                    mem = base_mem * 0.6 + random.uniform(-3, 10)
                    cost = base_cost * 0.5
                else:
                    cpu = min(100, base_cpu + random.uniform(0, 15))
                    mem = min(100, base_mem + random.uniform(0, 10))
                    cost = base_cost * (1 + (day - 80) * 0.1)
            else:
                cpu = max(0, min(100, base_cpu + random.uniform(-8, 8)))
                mem = max(0, min(100, base_mem + random.uniform(-8, 8)))
                cost = base_cost * random.uniform(0.95, 1.05)
            
            await db.execute('''
                INSERT INTO vm_history (vm_id, timestamp, cpu_utilization, memory_utilization, cost)
                VALUES (?, ?, ?, ?, ?)
            ''', (vm_id, timestamp, cpu, mem, cost))
    
    # Hidden costs data
    hidden_costs = [
        ("hc-egress", "network", "Egress Data Transfer", 12400, 9800, 2600, "controlled", "Network Optimizer", 79),
        ("hc-disks", "storage", "Unattached Disks", 8200, 8200, 8200, "eliminated", "Orphan Hunter", 100),
        ("hc-idle", "compute", "Idle VMs (Dev/Test)", 15600, 14000, 14000, "controlled", "Scheduler Agent", 90),
        ("hc-storage", "storage", "Over-provisioned Storage", 6800, 5400, 5400, "optimizing", "Storage Optimizer", 79),
        ("hc-license", "license", "License Overallocation", 9200, 7800, 7800, "controlled", "License Manager", 85),
        ("hc-snapshot", "storage", "Snapshot Retention", 4500, 3200, 3200, "optimizing", "Lifecycle Agent", 71),
    ]
    
    for hc in hidden_costs:
        await db.execute('''
            INSERT INTO hidden_costs (id, category, name, detected, mitigated, monthly_savings, status, managed_by, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', hc)
    
    # Mission critical workloads
    mission_critical = [
        ("mc-epic", "Epic EHR Integration", 45000, "full", "RI", 35, "protected"),
        ("mc-pacs", "PACS Imaging", 28000, "full", "RI", 40, "protected"),
        ("mc-lis", "Lab Information System", 12000, "full", "RI", 30, "protected"),
        ("mc-pharmacy", "Pharmacy/Pyxis", 8500, "full", "SP", 25, "protected"),
        ("mc-blood", "Blood Bank", 6200, "full", "RI", 45, "protected"),
        ("mc-tumor", "Tumor Board AI", 22000, "capacity", "SP", 50, "protected"),
    ]
    
    for mc in mission_critical:
        await db.execute('''
            INSERT INTO mission_critical (id, name, monthly_cost, protection_level, coverage_type, capacity_headroom, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', mc)
    
    # Initial alerts - 10 total: 1 investigating (red), 9 resolved (green) = 9/10 resolved
    alerts = [
        # 1 critical alert still being investigated (the red one)
        ("spike", "critical", "GPU-Training-Runaway", "GPU cluster cost spike detected - $847/hr exceeds $500/hr threshold", "+$847/hr", "investigating", now),
        # 9 resolved alerts (all green - showing system is working well)
        ("resolved", "medium", "Storage-Account-Logs", "Storage growth anomaly auto-resolved by lifecycle policy", "+$234", "auto-resolved", 
         (datetime.utcnow() - timedelta(hours=3)).isoformat()),
        ("resolved", "medium", "SQL-Prod-Primary", "SQL replication bandwidth spike resolved", "+$180", "auto-resolved",
         (datetime.utcnow() - timedelta(days=1)).isoformat()),
        ("resolved", "medium", "RHEL-App-Server-03", "Right-sizing recommendation applied successfully", "-$890", "auto-resolved",
         (datetime.utcnow() - timedelta(days=2)).isoformat()),
        ("resolved", "low", "Windows-Dev-Test-07", "Auto-shutdown schedule implemented", "-$1200", "auto-resolved",
         (datetime.utcnow() - timedelta(days=3)).isoformat()),
        ("resolved", "medium", "ASR-DR-Replica-02", "DR replication optimized", "-$450", "auto-resolved",
         (datetime.utcnow() - timedelta(days=4)).isoformat()),
        ("resolved", "low", "Storage-Archive-01", "Cold storage tiering applied", "-$320", "auto-resolved",
         (datetime.utcnow() - timedelta(days=5)).isoformat()),
        ("resolved", "medium", "AKS-Prod-Cluster", "Node pool auto-scaling optimized", "-$680", "auto-resolved",
         (datetime.utcnow() - timedelta(days=6)).isoformat()),
        ("resolved", "low", "Network-Egress-Monitor", "Egress optimization completed", "-$290", "auto-resolved",
         (datetime.utcnow() - timedelta(days=7)).isoformat()),
        ("resolved", "medium", "AVD-Session-Host-Pool", "AVD session host scaling optimized", "-$410", "auto-resolved",
         (datetime.utcnow() - timedelta(days=8)).isoformat()),
    ]
    
    for alert in alerts:
        await db.execute('''
            INSERT INTO alerts (type, severity, resource, message, delta, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', alert)
    
    # Historical anomalies for the past 30 days
    anomaly_history = [
        # GPU spike incident (the big one)
        ("GPU-Training-Runaway", "gpu-spike", "compute", "critical", 
         (datetime.utcnow() - timedelta(days=2)).isoformat(), 8470.0,
         "ML training job exceeded expected duration by 340% due to misconfigured checkpointing interval. Job was set to checkpoint every 100 steps but data pipeline stalled causing infinite retry loop.",
         "Scaled node pool from 8 to 2 GPU nodes, added 4-hour job timeout in ML pipeline, implemented cost cap at $500/hr with auto-termination.",
         "resolved", (datetime.utcnow() - timedelta(days=1, hours=18)).isoformat(),
         "Cost Sentinel + Recommendation Validator", "Cost Sentinel", 97.8),
        
        # SQL Always On replication cost spike
        ("SQL-Prod-Primary", "sql-replication", "database", "high",
         (datetime.utcnow() - timedelta(days=5)).isoformat(), 2340.0,
         "SQL Always On synchronous replication bandwidth exceeded baseline by 180% due to bulk data migration running during peak hours.",
         "Rescheduled bulk migrations to off-peak window (2-6 AM EST), implemented bandwidth throttling for non-critical replication traffic.",
         "resolved", (datetime.utcnow() - timedelta(days=4, hours=12)).isoformat(),
         "Spend Prophet", "Cost Sentinel", 94.2),
        
        # Storage egress burst
        ("Storage-Account-Logs", "egress-burst", "storage", "high",
         (datetime.utcnow() - timedelta(days=8)).isoformat(), 1890.0,
         "Cross-region data transfer spike caused by misconfigured backup job copying 15TB to secondary region hourly instead of daily.",
         "Fixed backup schedule from hourly to daily, enabled Azure Private Link for internal transfers, implemented egress monitoring alerts.",
         "resolved", (datetime.utcnow() - timedelta(days=7, hours=6)).isoformat(),
         "Storage Optimizer", "Cost Sentinel", 99.1),
        
        # RHEL VM right-sizing opportunity
        ("RHEL-App-Server-03", "rightsizing", "compute", "medium",
         (datetime.utcnow() - timedelta(days=12)).isoformat(), 890.0,
         "VM consistently running at 15% CPU utilization over 30-day period. D8s_v3 instance oversized for actual workload requirements.",
         "Downsized from D8s_v3 to D4s_v3, saving $890/month. Validated with 2-week monitoring period showing no performance degradation.",
         "resolved", (datetime.utcnow() - timedelta(days=10)).isoformat(),
         "Right-Size Engine", "Cost Validator", 96.5),
        
        # Windows VM idle detection
        ("Windows-Dev-Test-07", "idle-resource", "compute", "medium",
         (datetime.utcnow() - timedelta(days=15)).isoformat(), 1200.0,
         "Development VM running 24/7 but only accessed during business hours (9 AM - 6 PM EST). 62% of runtime is idle.",
         "Implemented auto-shutdown schedule (7 PM - 7 AM EST and weekends), reducing monthly cost by 62%.",
         "resolved", (datetime.utcnow() - timedelta(days=14)).isoformat(),
         "Orphan Hunter", "Cost Validator", 98.3),
        
        # ASR replication anomaly
        ("ASR-DR-Replication", "replication-cost", "disaster-recovery", "high",
         (datetime.utcnow() - timedelta(days=18)).isoformat(), 3200.0,
         "Azure Site Recovery replication costs spiked 250% due to high churn rate on database servers during month-end processing.",
         "Optimized replication schedule to exclude temp/log files, implemented application-consistent snapshots instead of crash-consistent.",
         "resolved", (datetime.utcnow() - timedelta(days=16)).isoformat(),
         "Cost Sentinel", "Recommendation Validator", 95.7),
        
        # Unattached disk cleanup
        ("Disk-Orphaned-Premium-SSD", "orphaned-resource", "storage", "low",
         (datetime.utcnow() - timedelta(days=20)).isoformat(), 450.0,
         "12 premium SSD disks found unattached after VM deletions. Disks were not cleaned up during decommissioning process.",
         "Deleted 12 orphaned disks after 7-day grace period verification. Implemented tagging policy requiring owner and expiry date.",
         "resolved", (datetime.utcnow() - timedelta(days=19)).isoformat(),
         "Orphan Hunter", "Cost Validator", 99.8),
        
        # AI/ML token overrun
        ("Azure-OpenAI-Prod", "token-overrun", "ai-ml", "critical",
         (datetime.utcnow() - timedelta(days=22)).isoformat(), 4500.0,
         "GPT-4 token consumption exceeded budget by 180% due to chatbot retry logic creating infinite conversation loops on error responses.",
         "Fixed retry logic with exponential backoff and max retry limit. Implemented token budget caps per conversation session.",
         "resolved", (datetime.utcnow() - timedelta(days=21)).isoformat(),
         "Cost Sentinel", "GPT-5", 98.9),
        
        # Network egress anomaly
        ("VNet-Hub-EastUS", "egress-anomaly", "network", "medium",
         (datetime.utcnow() - timedelta(days=25)).isoformat(), 1650.0,
         "Unexpected egress traffic to internet from hub VNet. Investigation revealed misconfigured NAT gateway routing internal traffic externally.",
         "Corrected NAT gateway rules, implemented Azure Firewall for egress filtering, added network flow logging for monitoring.",
         "resolved", (datetime.utcnow() - timedelta(days=24)).isoformat(),
         "Spend Prophet", "Cost Validator", 93.4),
        
        # RI utilization drop
        ("RI-Compute-Pool", "ri-underutilization", "commitment", "high",
         (datetime.utcnow() - timedelta(days=28)).isoformat(), 5200.0,
         "Reserved Instance utilization dropped to 45% after workload migration. 3-year RI commitment not being fully utilized.",
         "Exchanged underutilized D-series RIs for B-series to match new workload profile. Implemented RI utilization monitoring dashboard.",
         "resolved", (datetime.utcnow() - timedelta(days=26)).isoformat(),
         "Commitment Advisor", "Recommendation Validator", 96.1),
        
        # False positive - dismissed
        ("AKS-Prod-Cluster", "scaling-anomaly", "compute", "medium",
         (datetime.utcnow() - timedelta(days=10)).isoformat(), 0.0,
         "Detected unusual scaling pattern in AKS cluster. Investigation revealed this was expected behavior during planned load testing.",
         "Marked as false positive. Added load testing schedule to anomaly detection exclusion list.",
         "dismissed", (datetime.utcnow() - timedelta(days=10, hours=2)).isoformat(),
         "N/A", "Cost Sentinel", 0.0),
        
        # Currently investigating
        ("Cosmos-DB-Analytics", "throughput-spike", "database", "high",
         (datetime.utcnow() - timedelta(hours=6)).isoformat(), 1200.0,
         "Cosmos DB RU consumption increased 300% in last 6 hours. Investigating query patterns and partition key distribution.",
         None, "investigating", None,
         "Cost Sentinel", "Cost Sentinel", 89.5),
    ]
    
    for ah in anomaly_history:
        await db.execute('''
            INSERT INTO anomaly_history (resource, anomaly_type, category, severity, detected_at, cost_impact, root_cause, resolution, status, resolved_at, resolved_by, created_by_agent, validation_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ah)
    
    await db.commit()

# Global Azure service instances (Phase 1)
cost_service = None
recommendation_service = None
budget_service = None

@app.on_event("startup")
async def startup():
    global cost_service, recommendation_service, budget_service
    await init_db()
    
    # Initialize Phase 2 database if available
    if PHASE2_AVAILABLE:
        try:
            init_history_db()
            print("Phase 2 history database initialized")
        except Exception as e:
            print(f"Phase 2 database init failed: {e}")
    
    # Initialize Azure services if available and configured
    if AZURE_SERVICES_AVAILABLE:
        try:
            cost_service = CostService()
            recommendation_service = RecommendationService()
            budget_service = BudgetService()
            print("Azure services initialized successfully")
            
            # Start background scheduler if Phase 2 available
            if PHASE2_AVAILABLE:
                await start_scheduler()
                print("Background scheduler started with 4 jobs")
        except Exception as e:
            print(f"Azure services not configured: {e}")
            print("Running in demo mode with mock data")

@app.on_event("shutdown")
async def shutdown():
    if PHASE2_AVAILABLE:
        await stop_scheduler()
        print("Scheduler stopped")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Stats endpoint
@app.get("/api/stats")
async def get_stats():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT SUM(monthly_cost) FROM vms")
        total_cost = (await cursor.fetchone())[0] or 0
        
        cursor = await db.execute("SELECT SUM(potential_savings) FROM vms")
        total_savings = (await cursor.fetchone())[0] or 0
        
        cursor = await db.execute("SELECT COUNT(*) FROM vms")
        total_vms = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('investigating', 'new')")
        active_alerts = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT SUM(monthly_savings) FROM hidden_costs")
        hidden_mitigated = (await cursor.fetchone())[0] or 0
        
        # AdventHealth December 2025 MBR data
        # Daily Rate: $19.6K (+22% YoY), YTD ACR: $2.83M, MACC Goal: $20.3M
        return {
            "monthly_spend": 588000,  # $19.6K daily * 30 days
            "ai_savings": 20000,  # $20K/month AI-identified savings (conservative)
            "hidden_costs_found": 20000,  # AI-identified optimization opportunities
            "hidden_costs_mitigated": round(hidden_mitigated, 0),
            "ri_coverage": 4,  # Current actual RI coverage
            "sp_coverage": 0,  # Current SP coverage
            "target_coverage": 25,  # Target to increase to 25%
            "ri_savings_potential": 20000,  # Projected monthly savings at 25% RI coverage
            "budget_variance": 3.2,
            "forecast_accuracy": 97.2,
            "trust_score": 92,
            "agents_active": 9,  # 7 primary + 2 validators
            "anomalies_today": active_alerts,
            "todays_savings": 1500,  # Today's savings achieved
            "ytd_acr": 2830000,  # $2.83M YTD ACR
            "macc_goal": 20300000,  # $20.3M MACC Goal
            "macc_progress": 24.5,  # 24.5% of MACC goal
            "optimization_opportunity": 20000,  # Monthly optimization opportunity
            "yoy_growth": 22,  # +22% YoY
            "gpu_growth_mom": 97.6,  # 3P GPU +97.6% MoM
            "q2_conversion": 54,  # 54% Q2 conversion
        }

# VMs endpoint
@app.get("/api/vms")
async def get_vms():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM vms ORDER BY is_runaway DESC, monthly_cost DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/api/vms/{vm_id}/history")
async def get_vm_history(vm_id: str):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM vm_history WHERE vm_id = ? ORDER BY timestamp DESC LIMIT 30",
            (vm_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# Simulate tick - updates VM metrics
@app.post("/api/simulate-tick")
async def simulate_tick():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM vms")
        vms = await cursor.fetchall()
        
        updated = []
        for vm in vms:
            vm_dict = dict(vm)
            is_runaway = vm_dict["is_runaway"]
            
            if is_runaway:
                cpu_change = random.uniform(-3, 8)
                mem_change = random.uniform(-2, 6)
                cost_mult = random.uniform(0.95, 1.12)
            else:
                cpu_change = random.uniform(-2, 2)
                mem_change = random.uniform(-1.5, 1.5)
                cost_mult = random.uniform(0.99, 1.01)
            
            new_cpu = max(0, min(100, vm_dict["cpu_utilization"] + cpu_change))
            new_mem = max(0, min(100, vm_dict["memory_utilization"] + mem_change))
            new_cost = vm_dict["cost_per_hour"] * cost_mult
            
            await db.execute('''
                UPDATE vms SET cpu_utilization = ?, memory_utilization = ?, 
                              cost_per_hour = ?, last_updated = ?
                WHERE id = ?
            ''', (new_cpu, new_mem, new_cost, datetime.utcnow().isoformat(), vm_dict["id"]))
            
            vm_dict["cpu_utilization"] = round(new_cpu, 1)
            vm_dict["memory_utilization"] = round(new_mem, 1)
            vm_dict["cost_per_hour"] = round(new_cost, 2)
            updated.append(vm_dict)
        
        await db.commit()
        return updated

# Alerts
@app.get("/api/alerts")
async def get_alerts():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@app.post("/api/alerts/generate-demo")
async def generate_demo_alert():
    demo_alerts = [
        ("spike", "critical", "GPU-Training-Runaway", "Cost spike detected! GPU cluster exceeding $800/hr threshold", "+$847/hr"),
        ("anomaly", "high", "Storage-Account-Prod", "Unusual egress pattern detected - 3x normal traffic", "+$1,234"),
        ("warning", "medium", "AKS-Production", "Pod autoscaling triggered - monitoring cost impact", "+$156"),
        ("optimization", "low", "Web-Pool-01", "Right-sizing opportunity detected - 75% underutilized", "-$2,400/mo"),
        ("circuit", "critical", "GPU-Burst-Shield", "Circuit breaker TRIGGERED - auto-scaling down GPU cluster", "Protected"),
        ("savings", "info", "SQL-Prod-Primary", "3-Year RI recommendation validated - $45K annual savings", "$45,000"),
    ]
    
    alert = random.choice(demo_alerts)
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute('''
            INSERT INTO alerts (type, severity, resource, message, delta, status, timestamp)
            VALUES (?, ?, ?, ?, ?, 'new', ?)
        ''', (*alert, datetime.utcnow().isoformat()))
        await db.commit()
        
        return {
            "id": cursor.lastrowid,
            "type": alert[0],
            "severity": alert[1],
            "resource": alert[2],
            "message": alert[3],
            "delta": alert[4],
            "status": "new",
            "timestamp": datetime.utcnow().isoformat()
        }

# Hidden costs
@app.get("/api/hidden-costs")
async def get_hidden_costs():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM hidden_costs")
        rows = await cursor.fetchall()
        
        total_detected = sum(row["detected"] for row in rows)
        total_mitigated = sum(row["mitigated"] for row in rows)
        
        return {
            "total_detected": total_detected,
            "total_mitigated": total_mitigated,
            "recovery_rate": round((total_mitigated / total_detected) * 100, 0) if total_detected > 0 else 0,
            "categories": [dict(row) for row in rows]
        }

# Budgets
@app.get("/api/budgets")
async def get_budgets():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM budgets")
        rows = await cursor.fetchall()
        budgets = []
        for row in rows:
            budget = dict(row)
            # Map current/allocated to spent/budget for frontend compatibility
            spent = budget.get('current', 0)
            allocated = budget.get('allocated', 0)
            budget['spent'] = spent
            budget['budget'] = allocated
            # Calculate percentage and add threshold status
            if allocated > 0:
                pct = (spent / allocated) * 100
                budget['percentage'] = round(pct, 1)
                if pct >= 90:
                    budget['threshold_status'] = 'critical'
                    budget['threshold_message'] = f'CRITICAL: {pct:.0f}% of budget consumed'
                elif pct >= 80:
                    budget['threshold_status'] = 'warning'
                    budget['threshold_message'] = f'WARNING: {pct:.0f}% of budget consumed'
                elif pct >= 60:
                    budget['threshold_status'] = 'info'
                    budget['threshold_message'] = f'INFO: {pct:.0f}% of budget consumed'
                else:
                    budget['threshold_status'] = 'healthy'
                    budget['threshold_message'] = f'Healthy: {pct:.0f}% of budget consumed'
            else:
                budget['percentage'] = 0
                budget['threshold_status'] = 'healthy'
            budgets.append(budget)
        return budgets

# Mission critical
@app.get("/api/mission-critical")
async def get_mission_critical():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM mission_critical")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# AI Agents - diversified with primary and validator agents
@app.get("/api/agents")
async def get_agents():
    agents = [
        # Primary Agents
        {
            "id": "sentinel",
            "name": "Cost Sentinel",
            "type": "Real-Time Guardian",
            "role": "primary",
            "azure_service": "Azure Monitor + Logic Apps",
            "status": "active",
            "accuracy": 97.3,
            "last_action": "Detected GPU burst, triggered circuit breaker",
            "actions_today": 12,
            "savings_identified": 3200,
            "color": "#ef4444",
        },
        {
            "id": "commitment",
            "name": "Commitment Advisor",
            "type": "RI/SP Optimizer",
            "role": "primary",
            "azure_service": "Cost Management + Advisor",
            "status": "active",
            "accuracy": 94.8,
            "last_action": "Recommended 3-year RI for SQL cluster",
            "actions_today": 5,
            "savings_identified": 5800,
            "color": "#8b5cf6",
        },
        {
            "id": "orphan",
            "name": "Orphan Hunter",
            "type": "Waste Eliminator",
            "role": "primary",
            "azure_service": "Azure Advisor + Resource Graph",
            "status": "active",
            "accuracy": 99.1,
            "last_action": "Found 23 unattached disks ($2.1K/mo)",
            "actions_today": 8,
            "savings_identified": 2100,
            "color": "#f59e0b",
        },
        {
            "id": "rightsize",
            "name": "Right-Size Engine",
            "type": "Compute Optimizer",
            "role": "primary",
            "azure_service": "Azure Advisor + ML",
            "status": "active",
            "accuracy": 96.5,
            "last_action": "Downsized 4 VMs saving $3.1K/mo",
            "actions_today": 15,
            "savings_identified": 3100,
            "color": "#10b981",
        },
        # Validator/Secondary Agents
        {
            "id": "validator-cost",
            "name": "Cost Validator",
            "type": "Accuracy Checker",
            "role": "validator",
            "azure_service": "Azure AI Foundry",
            "status": "active",
            "accuracy": 98.2,
            "last_action": "Validated Sentinel anomaly detection",
            "actions_today": 24,
            "validates": "sentinel",
            "color": "#06b6d4",
        },
        {
            "id": "validator-recommendation",
            "name": "Recommendation Validator",
            "type": "Decision Auditor",
            "role": "validator",
            "azure_service": "Azure ML + Cost API",
            "status": "active",
            "accuracy": 97.8,
            "last_action": "Confirmed SQL 3yr RI recommendation",
            "actions_today": 10,
            "validates": "commitment",
            "color": "#ec4899",
        },
        {
            "id": "forecast",
            "name": "Spend Prophet",
            "type": "Predictive Forecaster",
            "role": "primary",
            "azure_service": "Azure ML + FOCUS",
            "status": "active",
            "accuracy": 91.2,
            "last_action": "Updated Q2 forecast: -8% vs budget",
            "actions_today": 3,
            "savings_identified": 0,
            "color": "#3b82f6",
        },
        {
            "id": "storage",
            "name": "Storage Optimizer",
            "type": "Tiering Agent",
            "role": "primary",
            "azure_service": "Storage Analytics + Lifecycle",
            "status": "active",
            "accuracy": 96.5,
            "last_action": "Moved 4.2TB to Archive tier",
            "actions_today": 2,
            "savings_identified": 1800,
            "color": "#14b8a6",
        },
        {
            "id": "gpt5",
            "name": "GPT-5",
            "type": "Advanced Reasoning",
            "role": "primary",
            "azure_service": "Azure OpenAI Service",
            "status": "active",
            "accuracy": 98.7,
            "last_action": "Analyzed complex multi-resource cost pattern",
            "actions_today": 18,
            "savings_identified": 4000,
            "color": "#d946ef",
            "model": "gpt-5",
            "endpoint": "https://pharma-agents-jnj-resource.cognitiveservices.azure.com",
        },
    ]
    return agents

# RI/SP Recommendations
@app.get("/api/recommendations")
async def get_recommendations():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT id, name, vm_type, monthly_cost, stability_score, growth_rate, 
                   recommendation, confidence, potential_savings
            FROM vms WHERE recommendation NOT IN ('INVESTIGATE', 'Auto-Shutdown', 'Rightsize')
            ORDER BY potential_savings DESC
        ''')
        rows = await cursor.fetchall()
        
        # Pricing structure for AdventHealth:
        # 1. MSRP (List Price) - Azure retail price
        # 2. EA Price = MSRP - 12% (AdventHealth Enterprise Agreement discount)
        # 3. RI/SP discounts are applied ON TOP of EA price:
        #    - 1-Year RI: 36% off EA price
        #    - 3-Year RI: 56% off EA price
        #    - 1-Year SP: 33% off EA price
        #    - 3-Year SP: 52% off EA price
        
        EA_DISCOUNT = 0.12  # AdventHealth's 12% Enterprise Agreement discount
        
        recommendations = []
        for row in rows:
            vm = dict(row)
            msrp = vm["monthly_cost"]  # This is the MSRP/List price
            rec = vm["recommendation"]
            
            # Calculate EA price (PAYG with 12% discount)
            ea_price = msrp * (1 - EA_DISCOUNT)
            
            # Calculate RI/SP discounts based on recommendation type
            # These are applied ON TOP of the EA price
            if "3-Year RI" in rec:
                ri_discount = 0.56
                sp_discount = 0.52
            elif "1-Year RI" in rec:
                ri_discount = 0.36
                sp_discount = 0.33
            elif "3-Year SP" in rec:
                ri_discount = 0.56
                sp_discount = 0.52
            else:  # 1-Year SP or other
                ri_discount = 0.36
                sp_discount = 0.33
            
            # Final prices with RI/SP applied to EA price
            ri_price = ea_price * (1 - ri_discount)
            sp_price = ea_price * (1 - sp_discount)
            
            # Savings compared to EA price (what they're currently paying)
            ri_savings = ea_price - ri_price
            sp_savings = ea_price - sp_price
            
            # Total savings compared to MSRP
            total_ri_savings = msrp - ri_price
            total_sp_savings = msrp - sp_price
            
            recommendations.append({
                "resource": vm["name"],
                "type": vm["vm_type"],
                "msrp": round(msrp, 0),  # List price
                "ea_price": round(ea_price, 0),  # PAYG + 12% EA discount (current price)
                "ea_discount": "12%",
                "ri_price": round(ri_price, 0),  # With RI on top of EA
                "sp_price": round(sp_price, 0),  # With SP on top of EA
                "ri_discount": f"{int(ri_discount * 100)}%",
                "sp_discount": f"{int(sp_discount * 100)}%",
                "monthly_cost": round(ea_price, 0),  # Current cost (EA price)
                "stability": vm["stability_score"],
                "recommendation": vm["recommendation"],
                "ri_savings": round(ri_savings, 0),  # Additional savings from RI vs EA
                "sp_savings": round(sp_savings, 0),  # Additional savings from SP vs EA
                "total_ri_savings": round(total_ri_savings, 0),  # Total savings vs MSRP
                "total_sp_savings": round(total_sp_savings, 0),  # Total savings vs MSRP
                "confidence": vm["confidence"],
                "reasoning": get_reasoning(vm)
            })
        
        return recommendations

def get_reasoning(vm):
    rec = vm["recommendation"]
    if "3-Year" in rec:
        return f"Extremely stable workload, consistent {vm['stability_score']}% stability over 90 days"
    elif "1-Year SP" in rec:
        return f"Growing workload with {vm['growth_rate']}% growth rate, needs flexibility"
    elif "1-Year RI" in rec:
        return f"Good stability ({vm['stability_score']}%) with moderate growth"
    return "Requires analysis"

# Automation controls
@app.get("/api/controls")
async def get_controls():
    return [
        {"id": "auto-rightsize", "name": "Auto-Rightsizing", "description": "Automatically resize underutilized VMs", "risk": "low", "enabled": True},
        {"id": "auto-shutdown", "name": "Dev/Test Auto-Shutdown", "description": "Stop non-prod VMs outside business hours", "risk": "low", "enabled": True},
        {"id": "orphan-cleanup", "name": "Orphan Cleanup", "description": "Remove unattached disks after 7 days", "risk": "low", "enabled": True},
        {"id": "storage-tiering", "name": "Storage Tiering", "description": "Move cold data to archive automatically", "risk": "low", "enabled": True},
        {"id": "spot-fallback", "name": "Spot Instance Fallback", "description": "Use Spot VMs for fault-tolerant workloads", "risk": "medium", "enabled": False},
        {"id": "ri-auto-purchase", "name": "RI Auto-Purchase", "description": "Auto-purchase RIs based on recommendations", "risk": "high", "enabled": False},
    ]

# Alert configurations
@app.get("/api/alert-config")
async def get_alert_config():
    return [
        {"id": "variance-10", "name": "10% Daily Variance", "channels": "Email + Slack", "severity": "warning", "enabled": True},
        {"id": "variance-15", "name": "15% Daily Variance", "channels": "Email + Slack + PagerDuty", "severity": "critical", "enabled": True},
        {"id": "budget-75", "name": "75% Budget Threshold", "channels": "Email", "severity": "info", "enabled": True},
        {"id": "budget-90", "name": "90% Budget Threshold", "channels": "Email + Slack", "severity": "warning", "enabled": True},
        {"id": "budget-100", "name": "100% Budget Threshold", "channels": "All Channels", "severity": "critical", "enabled": True},
        {"id": "anomaly", "name": "Anomaly Detected", "channels": "Email + Slack", "severity": "warning", "enabled": True},
    ]

# Forecast data
@app.get("/api/forecast")
async def get_forecast():
    return [
        {"month": "Jul", "actual": 265000, "predicted": 268000, "lower": 255000, "upper": 281000},
        {"month": "Aug", "actual": 272000, "predicted": 275000, "lower": 262000, "upper": 288000},
        {"month": "Sep", "actual": 268000, "predicted": 271000, "lower": 258000, "upper": 284000},
        {"month": "Oct", "actual": 258000, "predicted": 260000, "lower": 247000, "upper": 273000},
        {"month": "Nov", "actual": 252000, "predicted": 255000, "lower": 242000, "upper": 268000},
        {"month": "Dec", "actual": 248000, "predicted": 251000, "lower": 238000, "upper": 264000},
        {"month": "Jan", "actual": None, "predicted": 245000, "lower": 232000, "upper": 258000},
        {"month": "Feb", "actual": None, "predicted": 242000, "lower": 229000, "upper": 255000},
        {"month": "Mar", "actual": None, "predicted": 238000, "lower": 225000, "upper": 251000},
    ]

# Anomaly detection data for chart
@app.get("/api/anomaly-data")
async def get_anomaly_data():
    data = []
    base = 8500
    for i in range(12):
        date = (datetime.utcnow() - timedelta(days=11-i)).strftime("%m/%d")
        expected = base + random.uniform(-200, 200)
        
        if i == 3:  # Spike on day 4
            actual = 12800
            is_anomaly = True
        elif i == 9:  # Another spike
            actual = 11200
            is_anomaly = True
        else:
            actual = expected + random.uniform(-300, 300)
            is_anomaly = False
        
        data.append({
            "date": date,
            "actual": round(actual, 0),
            "expected": round(expected, 0),
            "is_anomaly": is_anomaly
        })
    
    return data

# Daily variance data
@app.get("/api/anomaly-history")
async def get_anomaly_history(days: int = 30, status: str = None):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM anomaly_history WHERE detected_at >= datetime('now', ?)"
        params = [f"-{days} days"]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY detected_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/api/variance-data")
async def get_variance_data():
    return [
        {"day": "Mon", "variance": 2.1},
        {"day": "Tue", "variance": -1.5},
        {"day": "Wed", "variance": 4.2},
        {"day": "Thu", "variance": 12.5},
        {"day": "Fri", "variance": -2.8},
        {"day": "Sat", "variance": 1.2},
        {"day": "Sun", "variance": -0.5},
    ]

# Chat endpoint (simulated AI)
@app.post("/api/chat")
async def chat(message: ChatMessage):
    user_msg = message.message.lower()
    
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        
        # Query anomaly history for context
        anomaly_cursor = await db.execute("SELECT * FROM anomaly_history ORDER BY detected_at DESC")
        anomalies = [dict(row) for row in await anomaly_cursor.fetchall()]
        
        # Query budgets for context
        budget_cursor = await db.execute("SELECT * FROM budgets")
        budgets_data = [dict(row) for row in await budget_cursor.fetchall()]
        
        # Calculate budget percentages
        for b in budgets_data:
            if b.get('allocated') and b.get('current'):
                b['percentage'] = round((b['current'] / b['allocated']) * 100, 1)
    
    # Data-aware responses based on actual database content
    if "anomal" in user_msg or "last month" in user_msg or "incident" in user_msg or "history" in user_msg:
        resolved = [a for a in anomalies if a['status'] == 'resolved']
        investigating = [a for a in anomalies if a['status'] == 'investigating']
        dismissed = [a for a in anomalies if a['status'] == 'dismissed']
        total_impact = sum(a['cost_impact'] or 0 for a in anomalies)
        
        top_incidents = sorted([a for a in anomalies if a['cost_impact']], key=lambda x: x['cost_impact'], reverse=True)[:3]
        top_list = "\n".join([f"  - {a['resource']} ({a['anomaly_type']}): ${a['cost_impact']:,.0f} - {a['status']}" for a in top_incidents])
        
        response = f"""Anomaly History Report (Last 30 Days)

Summary: {len(anomalies)} total anomalies detected
  - Resolved: {len(resolved)}
  - Investigating: {len(investigating)}
  - Dismissed (false positives): {len(dismissed)}
  - Total Cost Impact: ${total_impact:,.0f}

Top Incidents by Cost Impact:
{top_list}

All anomalies were detected by Cost Sentinel and validated by secondary agents (Cost Validator, Recommendation Validator, or GPT-5)."""

    elif "gpu" in user_msg or "spike" in user_msg or "runaway" in user_msg:
        gpu_anomalies = [a for a in anomalies if 'gpu' in a['resource'].lower() or 'gpu' in (a['anomaly_type'] or '').lower()]
        if gpu_anomalies:
            gpu = gpu_anomalies[0]
            response = f"""GPU Anomaly Analysis: {gpu['resource']}

Detected: {gpu['detected_at'][:10] if gpu['detected_at'] else 'N/A'}
Severity: {gpu['severity'].upper()}
Cost Impact: ${gpu['cost_impact']:,.0f}
Status: {gpu['status'].upper()}

Root Cause:
{gpu['root_cause']}

Resolution:
{gpu['resolution'] or 'Under investigation'}

Resolved By: {gpu['resolved_by'] or 'Pending'}
Validation Confidence: {gpu['validation_confidence']}%

This incident was detected by {gpu['created_by_agent']} and validated with {gpu['validation_confidence']}% confidence."""
        else:
            response = "No GPU-related anomalies found in the last 30 days."

    elif "sql" in user_msg or "3yr" in user_msg or "3 year" in user_msg or "database" in user_msg:
        sql_anomalies = [a for a in anomalies if 'sql' in a['resource'].lower() or 'database' in (a['category'] or '').lower()]
        if sql_anomalies:
            sql = sql_anomalies[0]
            response = f"""SQL/Database Analysis: {sql['resource']}

Recent Incident: {sql['anomaly_type']}
Cost Impact: ${sql['cost_impact']:,.0f}
Root Cause: {sql['root_cause']}
Resolution: {sql['resolution']}

RI Recommendation for SQL Workloads:
Based on 90 days of telemetry, SQL-Prod-Primary shows exceptional stability:
  - Stability Score: 98% (exceeds 85% threshold for 3-year commitments)
  - Growth Rate: Only 2% over 90 days
  - Recommendation: 3-Year Reserved Instance
  - Projected Savings: $45,000/year (56% discount vs PAYG)

Validated by Recommendation Validator with 97.8% confidence."""
        else:
            response = """SQL Workload Analysis

Based on 90 days of telemetry, SQL-Prod-Primary shows exceptional stability:
  - Stability Score: 98%
  - Growth Rate: 2% over 90 days
  - Recommendation: 3-Year Reserved Instance
  - Projected Savings: $45,000/year

Validated by Recommendation Validator with 97.8% confidence."""

    elif "ri" in user_msg or "coverage" in user_msg or "reserved" in user_msg:
        response = """RI/SP Coverage Analysis (AdventHealth)

Current State:
  - RI Coverage: 4% (significantly below best practice)
  - SP Coverage: 0%
  - Monthly Spend: $588K
  - Monthly RI Savings Target: $20,000

Target: Increase RI Coverage to 25%
  - Best Practice Target: 60-70% for stable workloads

Savings Breakdown at 25% RI Coverage:
  - SQL Always On: $80K/yr at 56% discount = $45K/yr savings
  - Rest of Infra: $1.18M/yr at 40% discount = $58K/yr savings
  - Windows Compute: $345K/yr at 35% discount = $28K/yr savings
  - Linux Compute: $106K/yr at 35% discount = $16K/yr savings

Recommended Action Plan:
  1. Phase 1 (Q1): Purchase 1-year RIs for SQL Always On workloads
  2. Phase 2 (Q2): Extend to stable Windows/Linux compute
  3. Phase 3 (Q3): Evaluate 3-year RIs for highest stability workloads

ROI Analysis:
  - Investment: ~$150K upfront (1-year RI)
  - Monthly Savings: $20,000
  - Payback: 12 months

Validated by Commitment Advisor and Recommendation Validator agents."""

    elif "budget" in user_msg or "spend" in user_msg or "over" in user_msg:
        budget_lines = []
        for b in budgets_data:
            pct = b.get('percentage', 0)
            status = 'CRITICAL' if pct >= 90 else 'WARNING' if pct >= 80 else 'INFO' if pct >= 60 else 'OK'
            budget_lines.append(f"  - {b['name']}: ${b['current']:,} / ${b['allocated']:,} - {status} ({pct}%)")
        
        budget_table = "\n".join(budget_lines)
        critical = [b for b in budgets_data if b.get('percentage', 0) >= 90]
        warning = [b for b in budgets_data if 80 <= b.get('percentage', 0) < 90]
        healthy = [b for b in budgets_data if b.get('percentage', 0) < 80]
        
        response = f"""Budget Health Summary (AdventHealth December 2025)

Budget Status:
{budget_table}

Summary: {len(healthy)} healthy, {len(warning)} warning, {len(critical)} critical

Alerts:
  - Critical (>90%): {len(critical)} budgets
  - Warning (>80%): {len(warning)} budgets

AdventHealth MBR Metrics:
  - Daily Rate: $19.6K (+22% YoY)
  - YTD ACR: $2.83M
  - MACC Goal: $20.3M (24.5% progress)
  - 3P GPU Growth: +97.6% MoM"""

    elif "saving" in user_msg or "cost" in user_msg:
        resolved_savings = sum(a['cost_impact'] or 0 for a in anomalies if a['status'] == 'resolved')
        response = f"""Cost Savings Summary (AdventHealth)

Monthly AI-Identified Savings: $20,000
Today's Savings Achieved: $1,500
Anomaly Resolution Savings: ${resolved_savings:,.0f}

Top Growth Areas (MoM):
- 3P GPU: +97.6% ($43K ACR)
- AVD: +181% YoY ($410K ACR)
- Azure AI: +199% YoY ($62K ACR)

AI Agent Savings This Month:
- Cost Sentinel: $8,200
- Orphan Hunter: $4,400
- Right-Size Engine: $3,900
- Storage Optimizer: $3,500

Total AI-identified savings: $20,000/month"""

    else:
        # Try to call live Claude API for general questions
        context = f"""AdventHealth December 2025 MBR Data:
- Monthly Azure Cost: $588K ($19.6K daily rate)
- YTD ACR: $2.83M
- RI Coverage: 4% (Target: 25%)
- Anomalies: {len(anomalies)} total, {len([a for a in anomalies if a['status'] == 'resolved'])} resolved
- Budgets: {len([b for b in budgets_data if b.get('percentage', 0) < 80])} healthy, {len([b for b in budgets_data if b.get('percentage', 0) >= 80])} at risk
- Top growth: 3P GPU +97.6% MoM, AVD +181% YoY, Azure AI +199% YoY"""
        
        gpt5_response = await call_gpt5_api(message.message, context)
        
        if gpt5_response:
            response = gpt5_response
        else:
            # Fallback if GPT-5 API fails
            resolved_count = len([a for a in anomalies if a['status'] == 'resolved'])
            total_count = len([a for a in anomalies if a['status'] != 'dismissed'])
            response = f"""AdventHealth FinOps AI Assistant (GPT-5)

I have access to your Azure subscription data and can answer questions about:

  - Anomalies: "Show me last month's anomalies" or "How was the GPU spike resolved?"
  - Budgets: "What's our budget status?" or "Which budgets are over 80%?"
  - Savings: "What were our total savings this month?"
  - RI Coverage: "Explain RI coverage recommendations"
  - SQL/Database: "Why 3-year RI for SQL?"

Quick Stats (December 2025 MBR):
  - Daily Rate: $19.6K (+22% YoY)
  - YTD ACR: $2.83M
  - Monthly Azure Cost: $588K
  - Anomalies: {resolved_count}/{total_count} resolved this month
  - RI Coverage: 4% (Target: 25%)
  - Monthly Savings: $20,000

All recommendations are validated by secondary AI agents for accuracy."""

    return {"response": response, "timestamp": datetime.utcnow().isoformat()}

# Azure Configuration endpoints
@app.get("/api/azure-config")
async def get_azure_config():
    if azure_config_store:
        return {
            "configured": True,
            "tenant_id": azure_config_store.get("tenant_id", "")[:8] + "..." if azure_config_store.get("tenant_id") else "",
            "client_id": azure_config_store.get("client_id", "")[:8] + "..." if azure_config_store.get("client_id") else "",
            "subscription_id": azure_config_store.get("subscription_id", "")[:8] + "..." if azure_config_store.get("subscription_id") else "",
            "has_secret": bool(azure_config_store.get("client_secret")),
            "last_discovery": azure_config_store.get("last_discovery"),
            "resources_discovered": azure_config_store.get("resources_discovered", 0)
        }
    return {"configured": False}

@app.post("/api/azure-config")
async def save_azure_config(config: AzureConfig):
    azure_config_store["tenant_id"] = config.tenant_id
    azure_config_store["client_id"] = config.client_id
    azure_config_store["client_secret"] = config.client_secret
    azure_config_store["subscription_id"] = config.subscription_id
    return {"success": True, "message": "Azure configuration saved successfully"}

@app.post("/api/azure-config/test")
async def test_azure_connection():
    if not azure_config_store.get("tenant_id"):
        return {"success": False, "message": "No Azure configuration found"}
    
    # Simulated connection test - in production would use Azure SDK
    await asyncio.sleep(1)  # Simulate API call
    return {
        "success": True,
        "message": "Successfully connected to Azure",
        "tenant_name": "AdventHealth Production",
        "subscription_name": "AH-Production-001"
    }

@app.post("/api/azure-config/discover")
async def discover_azure_resources():
    if not azure_config_store.get("tenant_id"):
        return {"success": False, "message": "No Azure configuration found"}
    
    # Simulated discovery - in production would use Azure Resource Graph
    await asyncio.sleep(2)  # Simulate discovery
    azure_config_store["last_discovery"] = datetime.utcnow().isoformat()
    azure_config_store["resources_discovered"] = 156
    
    return {
        "success": True,
        "message": "Discovery completed",
        "summary": {
            "virtual_machines": 47,
            "sql_databases": 12,
            "storage_accounts": 28,
            "kubernetes_clusters": 3,
            "app_services": 18,
            "networking": 34,
            "other": 14,
            "total": 156
        },
        "cost_summary": {
            "monthly_spend": 248000,
            "potential_savings": 89000,
            "ri_coverage": 35,
            "sp_coverage": 25
        }
    }

# Control configuration storage
control_settings = {
    "auto-shutdown": {"enabled": True, "schedule": "19:00-07:00", "timezone": "EST"},
    "ri-purchase": {"enabled": True, "auto_approve_under": 5000, "require_approval_over": 5000},
    "orphan-cleanup": {"enabled": True, "grace_period_days": 7, "auto_delete": False},
    "right-sizing": {"enabled": True, "threshold_percent": 30, "auto_apply": False},
    "budget-alerts": {"enabled": True, "thresholds": [75, 90, 100]},
    "circuit-breakers": {"enabled": True, "gpu_limit": 500, "egress_limit_tb": 10, "vm_sprawl_limit": 20}
}

@app.get("/api/control-settings")
async def get_control_settings():
    return control_settings

@app.put("/api/control-settings/{control_id}")
async def update_control_setting(control_id: str, settings: dict):
    if control_id in control_settings:
        control_settings[control_id].update(settings)
        return {"success": True, "message": f"Control '{control_id}' updated", "settings": control_settings[control_id]}
    return {"success": False, "message": f"Control '{control_id}' not found"}

@app.post("/api/controls/{control_id}/toggle")
async def toggle_control(control_id: str):
    if control_id in control_settings:
        control_settings[control_id]["enabled"] = not control_settings[control_id]["enabled"]
        return {"success": True, "enabled": control_settings[control_id]["enabled"]}
    return {"success": False, "message": f"Control '{control_id}' not found"}

# Circuit breaker settings
circuit_breaker_settings = {
    "gpu-burst": {"enabled": True, "threshold": 500, "unit": "$/hr", "action": "scale-to-zero"},
    "egress-flood": {"enabled": True, "threshold": 10, "unit": "TB/day", "action": "throttle"},
    "storage-tsunami": {"enabled": True, "threshold": 5, "unit": "%/day", "action": "pause-ingestion"},
    "vm-sprawl": {"enabled": True, "threshold": 20, "unit": "VMs/week", "action": "block-creation"},
    "ai-token-overrun": {"enabled": True, "threshold": 2000000, "unit": "tokens/hr", "action": "fallback-model"}
}

@app.get("/api/circuit-breakers")
async def get_circuit_breakers():
    return circuit_breaker_settings

@app.put("/api/circuit-breakers/{breaker_id}")
async def update_circuit_breaker(breaker_id: str, settings: dict):
    if breaker_id in circuit_breaker_settings:
        circuit_breaker_settings[breaker_id].update(settings)
        return {"success": True, "settings": circuit_breaker_settings[breaker_id]}
    return {"success": False, "message": f"Circuit breaker '{breaker_id}' not found"}


# ============ LIVE AZURE DATA ENDPOINTS (Phase 1) ============

@app.get("/api/azure/costs/daily")
async def get_azure_daily_costs(days: int = 30):
    """Get daily cost breakdown from Azure Cost Management."""
    if cost_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": cost_service.get_daily_costs(days), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching costs: {str(e)}")

@app.get("/api/azure/costs/by-service")
async def get_azure_costs_by_service(days: int = 30):
    """Get cost breakdown by Azure service."""
    if cost_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": cost_service.get_costs_by_service(days), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching costs: {str(e)}")

@app.get("/api/azure/costs/by-resource-group")
async def get_azure_costs_by_rg(days: int = 30):
    """Get cost breakdown by resource group."""
    if cost_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": cost_service.get_costs_by_resource_group(days), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching costs: {str(e)}")

@app.get("/api/azure/costs/summary")
async def get_azure_cost_summary():
    """Get monthly cost summary with MTD and forecast."""
    if cost_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": cost_service.get_monthly_summary(), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching summary: {str(e)}")

@app.get("/api/azure/recommendations")
async def get_azure_recommendations():
    """Get all RI/SP and Advisor cost recommendations."""
    if recommendation_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return recommendation_service.get_all_recommendations()
    except Exception as e:
        raise HTTPException(500, f"Error fetching recommendations: {str(e)}")

@app.get("/api/azure/recommendations/ri")
async def get_ri_recommendations():
    """Get Reserved Instance recommendations."""
    if recommendation_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": recommendation_service.get_reservation_recommendations(), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching RI recommendations: {str(e)}")

@app.get("/api/azure/recommendations/advisor")
async def get_advisor_recommendations():
    """Get Azure Advisor cost recommendations."""
    if recommendation_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return {"data": recommendation_service.get_advisor_cost_recommendations(), "source": "azure"}
    except Exception as e:
        raise HTTPException(500, f"Error fetching advisor recommendations: {str(e)}")

@app.get("/api/azure/ri-coverage")
async def get_ri_coverage():
    """Get current RI coverage percentage."""
    if recommendation_service is None:
        raise HTTPException(503, "Azure services not configured")
    try:
        return recommendation_service.get_ri_coverage()
    except Exception as e:
        raise HTTPException(500, f"Error fetching RI coverage: {str(e)}")

@app.get("/api/azure/health")
async def azure_health_check():
    """Check Azure connection health."""
    return {
        "cost_service": cost_service is not None,
        "recommendation_service": recommendation_service is not None,
        "budget_service": budget_service is not None,
        "status": "connected" if cost_service else "demo_mode"
    }


# ============ PHASE 2: HISTORICAL DATA ENDPOINTS ============

@app.get("/api/history/daily-costs")
async def get_historical_daily_costs(days: int = 30):
    """Get historical daily costs from local database."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    from datetime import date, timedelta
    
    with get_db() as db:
        cutoff = date.today() - timedelta(days=days)
        records = db.query(DailyCostHistory).filter(
            DailyCostHistory.date >= cutoff
        ).order_by(DailyCostHistory.date.asc()).all()
        
        return {
            "data": [
                {
                    "date": r.date.isoformat(),
                    "cost": r.total_cost,
                    "currency": r.currency
                }
                for r in records
            ],
            "source": "history",
            "record_count": len(records)
        }


@app.get("/api/history/cost-trend")
async def get_cost_trend(days: int = 90):
    """Get cost trend with week-over-week comparison."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    from datetime import date, timedelta
    
    with get_db() as db:
        cutoff = date.today() - timedelta(days=days)
        records = db.query(DailyCostHistory).filter(
            DailyCostHistory.date >= cutoff
        ).order_by(DailyCostHistory.date.asc()).all()
        
        if not records:
            return {"data": [], "trend": "insufficient_data"}
        
        # Calculate weekly averages
        weekly_data = {}
        for r in records:
            week = r.date.isocalendar()[1]
            year = r.date.year
            key = f"{year}-W{week:02d}"
            if key not in weekly_data:
                weekly_data[key] = []
            weekly_data[key].append(r.total_cost)
        
        weekly_avgs = {k: sum(v)/len(v) for k, v in weekly_data.items()}
        weeks = sorted(weekly_avgs.keys())
        
        # Calculate trend
        if len(weeks) >= 2:
            last_week = weekly_avgs[weeks[-1]]
            prev_week = weekly_avgs[weeks[-2]]
            wow_change = ((last_week - prev_week) / prev_week * 100) if prev_week > 0 else 0
            trend = "up" if wow_change > 5 else "down" if wow_change < -5 else "stable"
        else:
            wow_change = 0
            trend = "insufficient_data"
        
        return {
            "weekly_averages": [{"week": k, "avg_cost": round(v, 2)} for k, v in weekly_avgs.items()],
            "trend": trend,
            "wow_change_pct": round(wow_change, 1),
            "total_days": len(records)
        }


# ============ PHASE 2: ANOMALY ENDPOINTS ============

@app.get("/api/anomalies")
async def get_detected_anomalies(status: str = None, days: int = 30):
    """Get detected anomalies."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    from datetime import date, timedelta
    
    with get_db() as db:
        cutoff = date.today() - timedelta(days=days)
        query = db.query(AnomalyRecord).filter(
            AnomalyRecord.anomaly_date >= cutoff
        )
        
        if status:
            query = query.filter(AnomalyRecord.status == status)
        
        records = query.order_by(AnomalyRecord.detected_at.desc()).all()
        
        return {
            "anomalies": [
                {
                    "id": r.id,
                    "date": r.anomaly_date.isoformat(),
                    "metric": r.metric,
                    "actual": r.actual_value,
                    "baseline": r.baseline_value,
                    "variance_pct": r.variance_pct,
                    "variance_amount": r.variance_amount,
                    "severity": r.severity,
                    "status": r.status,
                    "root_cause": r.root_cause,
                    "detected_at": r.detected_at.isoformat()
                }
                for r in records
            ],
            "total": len(records),
            "open_count": sum(1 for r in records if r.status == "open")
        }


@app.patch("/api/anomalies/{anomaly_id}")
async def update_anomaly(anomaly_id: int, status: str = None, root_cause: str = None):
    """Update anomaly status or root cause."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    with get_db() as db:
        record = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()
        if not record:
            raise HTTPException(404, "Anomaly not found")
        
        if status:
            record.status = status
            if status == "resolved":
                record.resolved_at = datetime.utcnow()
        
        if root_cause:
            record.root_cause = root_cause
        
        db.commit()
        
        return {"success": True, "anomaly_id": anomaly_id}


# ============ PHASE 2: BUDGET ENDPOINTS ============

@app.get("/api/azure/budgets")
async def get_azure_budgets():
    """Get Azure Budget status."""
    if budget_service is None:
        raise HTTPException(503, "Budget service not configured")
    try:
        return budget_service.get_budget_summary()
    except Exception as e:
        raise HTTPException(500, f"Error fetching budgets: {str(e)}")


# ============ PHASE 2: SCHEDULER STATUS ============

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get background job status."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    sched = get_scheduler()
    jobs = []
    
    for job in sched.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": sched.running,
        "jobs": jobs
    }


@app.post("/api/scheduler/trigger/{job_id}")
async def trigger_job(job_id: str):
    """Manually trigger a background job."""
    if not PHASE2_AVAILABLE:
        raise HTTPException(503, "Phase 2 features not available")
    
    sched = get_scheduler()
    job = sched.get_job(job_id)
    
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    
    # Run immediately
    job.modify(next_run_time=datetime.utcnow())
    
    return {"success": True, "message": f"Job {job_id} triggered"}
