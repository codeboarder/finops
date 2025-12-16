/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback } from 'react'
import './App.css'
import { 
  Activity, TrendingUp, Shield, Zap, AlertTriangle, CheckCircle, 
  DollarSign, Bot, Target, Brain, Sparkles, 
  Search, Bell, RefreshCw, Settings, Clock,
  Cloud, Layers, Lock, Key, Globe, Server,
  Power, Sliders, MessageSquare, Send, X, Save, Play, Loader2, Database,
  Upload, FileText
} from 'lucide-react'
import { 
  Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ComposedChart
} from 'recharts'
import { Toaster, toast } from 'sonner'

// Use window.location.origin for tunnel access (avoids credentials in URL issue), or explicit VITE_API_URL if set
const rawApiUrl = import.meta.env.VITE_API_URL;
const API_URL = rawApiUrl && rawApiUrl.trim().length > 0 ? rawApiUrl : (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')

function App() {
  const [activeTab, setActiveTab] = useState('exec')
  const [stats, setStats] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [hiddenCosts, setHiddenCosts] = useState<any>(null)
  const [budgets, setBudgets] = useState<any[]>([])
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [controls, setControls] = useState<any[]>([])
  const [alertConfigs, setAlertConfigs] = useState<any[]>([])
  const [missionCritical, setMissionCritical] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [anomalyData, setAnomalyData] = useState<any[]>([])
  const [varianceData, setVarianceData] = useState<any[]>([])
  const [forecast, setForecast] = useState<any[]>([])
  const [currentTime, setCurrentTime] = useState(new Date())
  const [chatMessages, setChatMessages] = useState<any[]>([
    { role: 'assistant', content: "I'm your FinOps AI Assistant. Ask me about costs, recommendations, or anomalies." }
  ])
    const [chatInput, setChatInput] = useState('')
    const [chatOpen, setChatOpen] = useState(false)
    const [isLive, setIsLive] = useState(true)
    const [azureConfig, setAzureConfig] = useState({ tenant_id: '', client_id: '', client_secret: '', subscription_id: '' })
    const [azureStatus, setAzureStatus] = useState<any>(null)
    const [controlSettings, setControlSettings] = useState<any>({})
    const [circuitBreakers, setCircuitBreakers] = useState<any>({})
    const [isConnecting, setIsConnecting] = useState(false)
    const [isDiscovering, setIsDiscovering] = useState(false)
    const [discoveryResult, setDiscoveryResult] = useState<any>(null)
    const [selectedAlert, setSelectedAlert] = useState<any>(null)
    const [alertModalOpen, setAlertModalOpen] = useState(false)
    const [workflowStep, setWorkflowStep] = useState(0)
    const [investigationRunning, setInvestigationRunning] = useState(false)
                const [emailStage, setEmailStage] = useState<'idle' | 'preview' | 'sent'>('idle')
                const [dataSource, setDataSource] = useState<'azure' | 'demo'>('demo')
                const [detectedAnomalies, setDetectedAnomalies] = useState<any[]>([])
                const [schedulerStatus, setSchedulerStatus] = useState<any>(null)
                const [csvInput, setCsvInput] = useState('')
                const [isImporting, setIsImporting] = useState(false)
                const [importStatus, setImportStatus] = useState<any>(null)
                const [alertSettings, setAlertSettings] = useState({
                  anomaly: { enabled: true, threshold: 15 },
                  budget: { enabled: true, warningThreshold: 80, criticalThreshold: 90 },
                  circuitBreaker: { enabled: true, threshold: 500 },
                  costSpike: { enabled: true, threshold: 25 }
                })
                const [smartRecommendations, setSmartRecommendations] = useState<any>(null)
                const [workloads, setWorkloads] = useState<any[]>([])
                const [evaluations, setEvaluations] = useState<any[]>([])
                const [newEvaluation, setNewEvaluation] = useState({ name: '', vendor: '', affected_services: '', poc_score: 50, adoption_probability: 50, decision_date: '', workload_id: '' })
                const [selectedRec, setSelectedRec] = useState<any | null>(null)
                const [selectedDetails, setSelectedDetails] = useState<any | null>(null)
                const [isDrawerOpen, setIsDrawerOpen] = useState(false)
                const [isDetailsLoading, setIsDetailsLoading] = useState(false)
                const [isReevaluating, setIsReevaluating] = useState(false)
                const [workloadContext, setWorkloadContext] = useState('')
                // These will be used when integrating the tabbed drawer component
                // const [activeDrawerTab, setActiveDrawerTab] = useState('intelligence')
                // const [newContextNote, setNewContextNote] = useState('')
                // const [contextHistory, setContextHistory] = useState<any[]>([])
                                const [showReEvalPrompt, setShowReEvalPrompt] = useState(false)
                                const [reEvalTriggers, setReEvalTriggers] = useState({
                                  new_document: false,
                                  status_change: false,
                                  new_context: false,
                                  decision_date_passed: false,
                                  fresh_analysis: false
                                })
                                const [discountSettings, setDiscountSettings] = useState({
                                  ea_discount: 12,
                                  ri_1year_discount: 36,
                                  ri_3year_discount: 56,
                                  sp_1year_discount: 33,
                                  sp_3year_discount: 52
                                })
                                              const [rispActions, setRispActions] = useState<any>({ approved_count: 0, held_count: 0, blocked_count: 0, total_approved_savings: 0 })
                                              const [uploadedDocs, setUploadedDocs] = useState<{name: string, size: number, url: string}[]>([])

                            const fetchData = useCallback(async () => {
            try {
                            // Check Azure health first
                            try {
                              const healthRes = await fetch(`${API_URL}/api/azure/health`)
                              const health = await healthRes.json()
                              setDataSource(health.status === 'connected' ? 'azure' : 'demo')
                            } catch {
                              setDataSource('demo')
                            }
              
                            // Fetch Phase 2 data (anomalies and scheduler status)
                            try {
                              const anomalyRes = await fetch(`${API_URL}/api/anomalies?status=open`)
                              const anomalyData = await anomalyRes.json()
                              setDetectedAnomalies(anomalyData.anomalies || [])
                            } catch {
                              setDetectedAnomalies([])
                            }
              
                            try {
                              const schedRes = await fetch(`${API_URL}/api/scheduler/status`)
                              const schedData = await schedRes.json()
                              setSchedulerStatus(schedData)
                            } catch {
                              setSchedulerStatus(null)
                            }

                            // Fetch Phase 3 data (smart recommendations and intelligence status)
                            try {
                              const smartRes = await fetch(`${API_URL}/api/recommendations/smart`)
                              const smartData = await smartRes.json()
                              setSmartRecommendations(smartData)
                            } catch {
                              setSmartRecommendations(null)
                            }

                                                        // Fetch workloads and evaluations
                                                        try {
                                                          const wlRes = await fetch(`${API_URL}/api/workloads`)
                                                          const wlData = await wlRes.json()
                                                          setWorkloads(wlData.workloads || [])
                                                        } catch {
                                                          setWorkloads([])
                                                        }

                                                        try {
                                                          const evalRes = await fetch(`${API_URL}/api/evaluations`)
                                                          const evalData = await evalRes.json()
                                                          setEvaluations(evalData.evaluations || [])
                                                        } catch {
                                                          setEvaluations([])
                                                        }

                                                        // Fetch discount settings
                                                        try {
                                                          const discRes = await fetch(`${API_URL}/api/discount-settings`)
                                                          const discData = await discRes.json()
                                                          setDiscountSettings(discData)
                                                        } catch {
                                                          // Keep defaults
                                                        }

                                                        // Fetch RI/SP actions for Executive Summary
                                                        try {
                                                          const rispRes = await fetch(`${API_URL}/api/risp-actions`)
                                                          const rispData = await rispRes.json()
                                                          setRispActions(rispData)
                                                        } catch {
                                                          // Keep defaults
                                                        }
        
              const endpoints = ['stats', 'agents', 'hidden-costs', 'budgets', 'recommendations', 'controls', 'alert-config', 'mission-critical', 'alerts', 'anomaly-data', 'variance-data', 'forecast', 'azure-config', 'control-settings', 'circuit-breakers']
              const results = await Promise.all(endpoints.map(e => fetch(`${API_URL}/api/${e}`).then(r => r.json()).catch(() => null)))
      
        if (results[0]) setStats(results[0])
        if (results[1]) setAgents(results[1])
        if (results[2]) setHiddenCosts(results[2])
        if (results[3]) setBudgets(results[3])
        if (results[4]) setRecommendations(results[4])
        if (results[5]) setControls(results[5])
        if (results[6]) setAlertConfigs(results[6])
        if (results[7]) setMissionCritical(results[7])
        if (results[8]) setAlerts(results[8])
        if (results[9]) setAnomalyData(results[9])
        if (results[10]) setVarianceData(results[10])
        if (results[11]) setForecast(results[11])
        if (results[12]) setAzureStatus(results[12])
        if (results[13]) setControlSettings(results[13])
        if (results[14]) setCircuitBreakers(results[14])
      } catch (e) { console.error(e) }
    }, [])

  const simulateTick = useCallback(async () => {
    if (!isLive) return
    try {
      await fetch(`${API_URL}/api/simulate-tick`, { method: 'POST' })
      const res = await fetch(`${API_URL}/api/anomaly-data`)
      setAnomalyData(await res.json())
    } catch (e) { console.error(e) }
  }, [isLive])

  const openAlertWorkflow = useCallback((alert: any) => {
    setSelectedAlert(alert)
    setAlertModalOpen(true)
    setWorkflowStep(0)
    setInvestigationRunning(false)
    setEmailStage('idle')
  }, [])

  const showAlertToast = useCallback((alert: any) => {
    const severityColors = alert.severity === 'critical' 
      ? 'border-red-500/40 bg-red-500/10' 
      : alert.severity === 'high' 
      ? 'border-yellow-500/40 bg-yellow-500/10' 
      : 'border-blue-500/40 bg-blue-500/10'
    const iconColor = alert.severity === 'critical' ? 'text-red-400' : alert.severity === 'high' ? 'text-yellow-400' : 'text-blue-400'
    
    toast.custom((id) => (
      <button
        onClick={() => {
          openAlertWorkflow(alert)
          toast.dismiss(id)
        }}
        className={`flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left hover:bg-slate-700 transition-colors cursor-pointer ${severityColors}`}
      >
        <AlertTriangle className={`mt-0.5 h-4 w-4 flex-shrink-0 ${iconColor}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white">{alert.message}</p>
          <p className="text-xs text-slate-400">{alert.resource} | {alert.delta}</p>
        </div>
        <span className="text-xs text-slate-500 whitespace-nowrap">Click to investigate</span>
      </button>
    ), { duration: 8000 })
  }, [openAlertWorkflow])

  const generateDemoAlert = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/alerts/generate-demo`, { method: 'POST' })
      const newAlert = await res.json()
      setAlerts(prev => [newAlert, ...prev])
      showAlertToast(newAlert)
    } catch (e) { console.error(e) }
  }, [showAlertToast])

  const handleChat = async () => {
    if (!chatInput.trim()) return
    const msg = chatInput
    setChatMessages(prev => [...prev, { role: 'user', content: msg }])
    setChatInput('')
    try {
      const res = await fetch(`${API_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) })
      const data = await res.json()
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to AI.' }])
    }
  }

  useEffect(() => {
    fetchData()
    const d = setInterval(fetchData, 300000)
    const t = setInterval(simulateTick, 30000)
    const c = setInterval(() => setCurrentTime(new Date()), 1000)
    // Disable demo alerts - they're distracting and not real data
    // const a = setTimeout(generateDemoAlert, 5000)
    // const alertInterval = setInterval(generateDemoAlert, 60000)
    return () => { clearInterval(d); clearInterval(t); clearInterval(c) }
  }, [fetchData, simulateTick])


  const getRecommendationsForAlert = (alert: any) => {
    const msg = (alert?.message || '').toLowerCase()
    const resource = (alert?.resource || '').toLowerCase()
    
    if (resource.includes('gpu') || msg.includes('gpu')) {
      return [
        { title: 'Scale down GPU node pool or pause training job', action: 'Scale Down' },
        { title: 'Enable GPU Burst Shield circuit breaker', action: 'Enable Shield' },
        { title: 'Move workloads to off-peak training window (nights/weekends)', action: 'Schedule' },
        { title: 'Review batch job configuration for cost optimization', action: 'Review' },
      ]
    }
    if (msg.includes('egress') || resource.includes('storage') || msg.includes('storage')) {
      return [
        { title: 'Review recent data export jobs and cross-region transfers', action: 'Audit' },
        { title: 'Enable Azure Storage lifecycle rules for cold data', action: 'Configure' },
        { title: 'Consider Private Endpoints to reduce egress costs', action: 'Implement' },
        { title: 'Set up egress monitoring alerts', action: 'Monitor' },
      ]
    }
    if (msg.includes('underutilized') || msg.includes('right-sizing') || (alert?.delta || '').toString().startsWith('-')) {
      return [
        { title: 'Downsize VM SKU to match actual utilization', action: 'Resize' },
        { title: 'Schedule auto-shutdown for non-production hours', action: 'Schedule' },
        { title: 'Move to B-series burstable instances', action: 'Migrate' },
        { title: 'Review 30-day CPU/memory metrics', action: 'Analyze' },
      ]
    }
    if (msg.includes('ri') || msg.includes('savings') || msg.includes('commitment')) {
      return [
        { title: 'Purchase 1-year or 3-year RI based on stability', action: 'Purchase RI' },
        { title: 'Target 60-70% RI coverage per best practices', action: 'Plan' },
        { title: 'Validate with Recommendation Validator agent', action: 'Validate' },
        { title: 'Review instance flexibility options', action: 'Review' },
      ]
    }
    return [
      { title: 'Review 30-day cost trend in Cost Management', action: 'Analyze' },
      { title: 'Check Azure Advisor recommendations', action: 'Review' },
      { title: 'Verify resource tagging and cost center', action: 'Tag' },
      { title: 'Assess business criticality level', action: 'Assess' },
    ]
  }

  const getOwnerEmail = (alert: any) => {
    const resource = (alert?.resource || 'unknown').toLowerCase().replace(/[^a-z0-9]/g, '-')
    return `${resource}-owner@emaildomain.org`
  }

  const handleAlertAction = async (action: string) => {
    if (!selectedAlert) return
    
    if (action === 'investigate') {
      setAlerts(prev => prev.map(a => a.id === selectedAlert.id ? { ...a, status: 'investigating' } : a))
      setInvestigationRunning(true)
      setWorkflowStep(1)
      toast.info('Investigation started', { description: 'Cost Sentinel + Validator agents assigned' })
      
      // Simulate async step progression
      setTimeout(() => setWorkflowStep(2), 1500)
      setTimeout(() => setWorkflowStep(3), 3000)
      setTimeout(() => {
        setWorkflowStep(4)
        setInvestigationRunning(false)
        toast.success('Investigation complete', { description: 'Recommendations ready - review actions below' })
      }, 4500)
      return
    }
    
    if (action === 'notify') {
      setEmailStage('preview')
      return
    }
    
    if (action === 'send-email') {
      setEmailStage('sent')
      setAlerts(prev => prev.map(a => a.id === selectedAlert.id ? { ...a, status: 'owner-notified' } : a))
      toast.success('Email sent to resource owner (simulated)', { description: getOwnerEmail(selectedAlert) })
      return
    }

    const actionMessages: any = {
      acknowledge: 'Alert acknowledged - Added to tracking queue',
      remediate: 'Auto-remediation triggered - Circuit breaker activated',
      dismiss: 'Alert dismissed - Marked as false positive',
      escalate: 'Escalated to FinOps team via PagerDuty'
    }
    toast.success(actionMessages[action] || 'Action completed', { description: selectedAlert.resource })
    setAlerts(prev => prev.map(a => a.id === selectedAlert.id ? { ...a, status: action === 'dismiss' ? 'dismissed' : action === 'remediate' ? 'auto-resolved' : 'investigating' } : a))
    setAlertModalOpen(false)
    setSelectedAlert(null)
  }

    const tabs = [
      { id: 'exec', label: 'Executive Summary', icon: TrendingUp },
      { id: 'command', label: 'Command Center', icon: Activity },
      { id: 'agents', label: 'AI Agents', icon: Bot },
      { id: 'hidden', label: 'Hidden Cost Hunter', icon: Search },
      { id: 'budget', label: 'Budget Guardrails', icon: Shield },
      { id: 'risp', label: 'RI/SP Optimizer', icon: Target },
      { id: 'controls', label: 'Controls & Alerts', icon: Sliders },
      { id: 'mission', label: 'Mission Critical', icon: Lock },
      { id: 'settings', label: 'Settings', icon: Settings },
    ]

    const [execChatMessages, setExecChatMessages] = useState<any[]>([
      { role: 'assistant', content: "Welcome to the Executive Summary. I have access to your Azure subscription data and can answer questions about costs, anomalies, savings opportunities, and budget status. What would you like to know?" }
    ])
    const [execChatInput, setExecChatInput] = useState('')
        const [selectedAgent, setSelectedAgent] = useState('gpt5')
        const availableAgents = [
          { id: 'gpt5', name: 'Azure FinOps Copilot', model: 'GPT-5', connected: true },
          { id: 'gpt-4', name: 'GPT-4 Turbo', model: 'GPT-4', connected: false },
          { id: 'gemini', name: 'Gemini Pro', model: 'Gemini', connected: false },
        ]

    const handleExecChat = async (directQuery?: string) => {
      const msg = directQuery || execChatInput
      if (!msg.trim()) return
      setExecChatMessages(prev => [...prev, { role: 'user', content: msg }])
      setExecChatInput('')
      try {
        const res = await fetch(`${API_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg, context: 'executive' }) })
        const data = await res.json()
        setExecChatMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } catch {
        setExecChatMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to AI.' }])
      }
    }

    // Quick questions moved to inline query buttons in Executive Summary

    const saveAzureConfig = async () => {
      setIsConnecting(true)
      try {
        await fetch(`${API_URL}/api/azure-config`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(azureConfig) })
        const testRes = await fetch(`${API_URL}/api/azure-config/test`, { method: 'POST' })
        const testData = await testRes.json()
        if (testData.success) {
          toast.success('Azure connection successful', { description: testData.tenant_name })
          setAzureStatus({ configured: true, ...testData })
        } else {
          toast.error('Connection failed', { description: testData.message })
        }
      } catch { toast.error('Failed to save configuration') }
      setIsConnecting(false)
    }

    const runDiscovery = async () => {
      setIsDiscovering(true)
      try {
        const res = await fetch(`${API_URL}/api/azure-config/discover_prod`, { method: 'POST' })
        const data = await res.json()
        if (data.success) {
          setDiscoveryResult(data)
          toast.success('Discovery completed', { description: `Found ${data.summary.total} resources` })
        } else {
          toast.error('Discovery failed', { description: data.message })
        }
      } catch { toast.error('Discovery failed') }
      setIsDiscovering(false)
    }

    const toggleControl = async (controlId: string) => {
      try {
        const res = await fetch(`${API_URL}/api/controls/${controlId}/toggle`, { method: 'POST' })
        const data = await res.json()
        if (data.success) {
          setControlSettings((prev: any) => ({ ...prev, [controlId]: { ...prev[controlId], enabled: data.enabled } }))
          toast.success(`Control ${data.enabled ? 'enabled' : 'disabled'}`)
        }
      } catch { toast.error('Failed to toggle control') }
    }

        const updateCircuitBreaker = async (breakerId: string, threshold: number) => {
          try {
            await fetch(`${API_URL}/api/circuit-breakers/${breakerId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ threshold }) })
            setCircuitBreakers((prev: any) => ({ ...prev, [breakerId]: { ...prev[breakerId], threshold } }))
            toast.success('Circuit breaker updated')
          } catch (e) { toast.error('Failed to update') }
        }

        const saveDiscountSettings = async () => {
          try {
            await fetch(`${API_URL}/api/discount-settings`, { 
              method: 'PUT', 
              headers: { 'Content-Type': 'application/json' }, 
              body: JSON.stringify(discountSettings) 
            })
            toast.success('Discount settings saved - prices will update on next refresh')
            fetchData() // Refresh recommendations with new discounts
          } catch (e) { 
            toast.error('Failed to save discount settings') 
          }
        }

        const recordRispAction = async (action: string, recommendation: any) => {
          try {
            await fetch(`${API_URL}/api/risp-actions/${action}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                resource: recommendation.resource,
                type: recommendation.type,
                savings: recommendation.ri_savings || recommendation.sp_savings || 0,
                recommendation: recommendation.recommendation
              })
            })
            toast.success(`Recommendation ${action}ed`)
            fetchData() // Refresh to update Executive Summary
          } catch (e) {
            toast.error(`Failed to ${action} recommendation`)
          }
        }

        const importCsvData = async () => {
      if (!csvInput.trim()) {
        toast.error('Please paste CSV data first')
        return
      }
      setIsImporting(true)
      try {
        // Parse CSV - Azure Advisor format
        const lines = csvInput.trim().split('\n')
        const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim())
        const recommendations: any[] = []
        
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].match(/(".*?"|[^",]+)(?=\s*,|\s*$)/g)?.map(v => v.replace(/"/g, '').trim()) || []
          if (values.length < 2) continue
          
          const row: any = {}
          headers.forEach((h, idx) => { row[h] = values[idx] || '' })
          
          // Map Azure Advisor CSV to our format
          const savings = parseFloat(row['Potential Annual Cost Savings'] || row['Annual Savings'] || '0')
          const monthlySavings = savings / 12
          
          recommendations.push({
            vm_name: row['Resource Name'] || row['Recommendation'] || 'Unknown Resource',
            vm_size: row['Type'] || 'Compute',
            region: row['Region'] || 'All Regions',
            os_type: row['OS Type'] || 'All',
            term: row['Term'] || '3-Year',
            recommendation_type: row['Recommendation']?.includes('savings plan') ? 'SP' : 'RI',
            current_monthly_cost: monthlySavings * 2,
            recommended_monthly_cost: monthlySavings,
            monthly_savings: monthlySavings,
            annual_savings: savings
          })
        }
        
        if (recommendations.length === 0) {
          toast.error('No valid recommendations found in CSV')
          setIsImporting(false)
          return
        }
        
        const res = await fetch(`${API_URL}/api/offline/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ri_recommendations: recommendations, daily_costs: [], budgets: [] })
        })
        const data = await res.json()
        
        if (data.success) {
          setImportStatus(data)
          toast.success(`Imported ${data.imported.ri_recommendations} recommendations`)
          setCsvInput('')
          fetchData()
        } else {
          toast.error('Import failed')
        }
      } catch (e) {
        toast.error('Failed to parse CSV')
        console.error(e)
      }
      setIsImporting(false)
    }

  const fmt = (v?: number | null) => {
    const n = typeof v === 'number' && !Number.isNaN(v) ? v : 0
    return n >= 1000000 ? `$${(n/1000000).toFixed(1)}M` : n >= 1000 ? `$${(n/1000).toFixed(0)}K` : `$${n.toFixed(0)}`
  }

  const createEvaluation = async () => {
    if (!newEvaluation.name || !newEvaluation.vendor || !newEvaluation.workload_id) {
      toast.error('Please enter evaluation name, vendor, and select a workload')
      return
    }
    try {
      const formData = new FormData()
      formData.append('workload_id', newEvaluation.workload_id)
      formData.append('name', newEvaluation.name)
      formData.append('vendor', newEvaluation.vendor)
      formData.append('evaluation_type', 'saas_replacement')
      formData.append('status', 'evaluating')
      if (newEvaluation.decision_date) formData.append('decision_date', newEvaluation.decision_date)
      formData.append('adoption_probability_pct', String(newEvaluation.adoption_probability))
      if (newEvaluation.poc_score) formData.append('poc_success_score', String(newEvaluation.poc_score))
      formData.append('hold_commitments', 'true')
      if (newEvaluation.affected_services) {
        formData.append('affected_azure_services', JSON.stringify(newEvaluation.affected_services.split(',').map(s => s.trim()).filter(Boolean)))
      }
      
      const res = await fetch(`${API_URL}/api/evaluations`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.id) {
        toast.success(`Evaluation "${newEvaluation.name}" created`)
        setNewEvaluation({ name: '', vendor: '', affected_services: '', poc_score: 50, adoption_probability: 50, decision_date: '', workload_id: '' })
        fetchData()
      }
    } catch (e) {
      toast.error('Failed to create evaluation')
    }
  }

  const deleteEvaluation = async (id: string) => {
    try {
      await fetch(`${API_URL}/api/evaluations/${id}`, { method: 'DELETE' })
      toast.success('Evaluation deleted')
      fetchData()
    } catch (e) {
      toast.error('Failed to delete evaluation')
    }
  }

  const openRecommendationDrawer = async (rec: any) => {
    setSelectedRec(rec)
    setIsDrawerOpen(true)
    setIsDetailsLoading(true)
    setWorkloadContext('')
    try {
      const res = await fetch(`${API_URL}/api/recommendations/${rec.id || rec.resource_id || 'demo'}/details`)
      const details = await res.json()
      setSelectedDetails(details)
      if (details.workload?.id) {
        const ctxRes = await fetch(`${API_URL}/api/workloads/${details.workload.id}/context`)
        const ctxData = await ctxRes.json()
        if (ctxData.context?.length > 0) {
          setWorkloadContext(ctxData.context[0].content)
        }
      }
    } catch (e) {
      console.error(e)
      setSelectedDetails(null)
    } finally {
      setIsDetailsLoading(false)
    }
  }

  const openReEvalPrompt = () => {
    if (!selectedRec || !selectedDetails?.evaluation?.id) {
      toast.error('No evaluation linked to this recommendation')
      return
    }
    setReEvalTriggers({
      new_document: false,
      status_change: false,
      new_context: false,
      decision_date_passed: false,
      fresh_analysis: false
    })
    setShowReEvalPrompt(true)
  }

  const handleReevaluate = async () => {
    if (!selectedRec || !selectedDetails?.evaluation?.id) {
      toast.error('No evaluation linked to this recommendation')
      return
    }
    setShowReEvalPrompt(false)
    setIsReevaluating(true)
    
    // Determine trigger based on checkboxes
    let trigger = 'manual'
    const focusAreas: string[] = []
    
    if (reEvalTriggers.new_document) {
      trigger = 'new_document'
      focusAreas.push('security_review', 'poc_metrics')
    }
    if (reEvalTriggers.status_change) {
      trigger = 'status_change'
      focusAreas.push('timeline', 'executive_support')
    }
    if (reEvalTriggers.new_context) {
      trigger = 'new_context'
      focusAreas.push('executive_support', 'budget')
    }
    if (reEvalTriggers.decision_date_passed) {
      trigger = 'decision_date_passed'
      focusAreas.push('timeline')
    }
    if (reEvalTriggers.fresh_analysis) {
      trigger = 'manual'
    }
    
    try {
      // Get previous analysis ID if exists
      const previousAnalysisId = selectedDetails?.agent_analysis?.id || null
      
      await fetch(`${API_URL}/api/evaluations/${selectedDetails.evaluation.id}/analyze`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger,
          focus_areas: focusAreas.length > 0 ? focusAreas : null,
          previous_analysis_id: previousAnalysisId
        })
      })
      const res = await fetch(`${API_URL}/api/recommendations/${selectedRec.id || selectedRec.resource_id || 'demo'}/details`)
      const details = await res.json()
      setSelectedDetails(details)
      toast.success('Recommendation re-evaluated with AI agents')
      fetchData()
    } catch (e) {
      console.error(e)
      toast.error('Failed to re-evaluate')
    } finally {
      setIsReevaluating(false)
    }
  }

  const saveWorkloadContext = async () => {
    if (!selectedDetails?.workload?.id || !workloadContext.trim()) {
      toast.error('Please enter context and ensure workload is linked')
      return
    }
    try {
      const formData = new FormData()
      formData.append('content', workloadContext)
      formData.append('added_by', 'user')
      await fetch(`${API_URL}/api/workloads/${selectedDetails.workload.id}/context`, {
        method: 'POST',
        body: formData
      })
      toast.success('Application context saved')
    } catch (e) {
      toast.error('Failed to save context')
    }
  }

  const setOverride = async (action: string, reason: string) => {
    if (!selectedRec) return
    try {
      const formData = new FormData()
      formData.append('action', action)
      formData.append('reason', reason)
      formData.append('override_by', 'user')
      await fetch(`${API_URL}/api/recommendations/${selectedRec.id || selectedRec.resource_id || 'demo'}/override`, {
        method: 'POST',
        body: formData
      })
      toast.success(`Override set: ${action.toUpperCase()}`)
      fetchData()
      setIsDrawerOpen(false)
    } catch (e) {
      toast.error('Failed to set override')
    }
  }

  const handleDocumentUpload = async (files: File[]) => {
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    const validFiles = files.filter(f => validTypes.includes(f.type) || f.name.match(/\.(pdf|doc|docx|xls|xlsx)$/i))
    
    if (validFiles.length === 0) {
      toast.error('Please upload PDF, Word, or Excel files only')
      return
    }
    
    for (const file of validFiles) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('resource_id', selectedRec?.id || selectedRec?.resource_id || 'demo')
        
        const res = await fetch(`${API_URL}/api/documents/upload`, {
          method: 'POST',
          body: formData
        })
        
        if (res.ok) {
          const data = await res.json()
          setUploadedDocs(prev => [...prev, { name: file.name, size: file.size, url: data.url || '#' }])
          toast.success(`Uploaded: ${file.name}`)
        } else {
          // For demo mode, simulate successful upload
          setUploadedDocs(prev => [...prev, { name: file.name, size: file.size, url: URL.createObjectURL(file) }])
          toast.success(`Uploaded: ${file.name}`)
        }
      } catch (e) {
        // For demo mode, simulate successful upload
        setUploadedDocs(prev => [...prev, { name: file.name, size: file.size, url: URL.createObjectURL(file) }])
        toast.success(`Uploaded: ${file.name}`)
      }
    }
  }

  const getAllSmartRecs = () => {
    if (!smartRecommendations) return []
    const all = [
      ...(smartRecommendations.approved || []).map((r: any) => ({ ...r, _action: 'approve' })),
      ...(smartRecommendations.modified || []).map((r: any) => ({ ...r, _action: 'modify' })),
      ...(smartRecommendations.hold || []).map((r: any) => ({ ...r, _action: 'hold' })),
      ...(smartRecommendations.blocked || []).map((r: any) => ({ ...r, _action: 'block' }))
    ]
    return all
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-gray-100">
      <Toaster position="top-right" theme="dark" richColors />
      
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Cloud className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">FinOps AI Command Center</h1>
                <p className="text-xs text-slate-400">ContosoHealth Azure Cost Intelligence</p>
              </div>
              <button onClick={() => setIsLive(!isLive)} className={`ml-4 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${isLive ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-slate-700 text-slate-400'}`}>
                <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`} />
                LIVE
              </button>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-center"><p className="text-xs text-slate-400">Today's Savings</p><p className="text-lg font-bold text-green-400">${stats?.todays_savings?.toLocaleString() || '0'}</p></div>
              <div className="text-center"><p className="text-xs text-slate-400">Agents Active</p><p className="text-lg font-bold text-blue-400">{stats?.agents_active || 0}</p></div>
              <div className="text-center"><p className="text-xs text-slate-400">Anomalies Today</p><p className="text-lg font-bold text-orange-400">{stats?.anomalies_today || 0}</p></div>
              <div className="text-right"><p className="text-xs text-slate-400">{currentTime.toLocaleDateString()}</p><p className="text-sm font-mono text-white">{currentTime.toLocaleTimeString()}</p></div>
            </div>
          </div>
          <div className="flex gap-1 mt-4">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}>
                <tab.icon className="w-4 h-4" />{tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="p-6">
        {activeTab === 'exec' && stats && (
          <div className="space-y-6">
            {/* Key Metrics Row */}
            <div className="grid grid-cols-6 gap-4">
              {[
                { label: 'MONTHLY AZURE COST', value: fmt(stats.monthly_spend), sub: `${fmt(stats.monthly_spend / 30)} daily rate`, icon: TrendingUp, color: 'blue' },
                { label: 'MONTHLY SAVINGS', value: fmt(stats.ai_savings), change: stats.data_source === 'azure_live' ? 'Live Azure Data' : '+$127K vs last month', icon: DollarSign, color: 'green' },
                                { label: 'ANOMALIES RESOLVED', value: stats?.data_source === 'azure_live' ? 'N/A' : `${alerts.filter((a: any) => a.status === 'auto-resolved' || a.status === 'owner-notified').length}/${alerts.length}`, sub: stats?.data_source === 'azure_live' ? 'No anomaly data' : 'This month', icon: CheckCircle, color: 'blue' },
                                { label: 'BUDGET STATUS', value: stats?.data_source === 'azure_live' ? 'N/A' : 'ON TRACK', sub: stats?.data_source === 'azure_live' ? 'No budget data' : `${budgets.filter((b: any) => b.threshold_status === 'healthy' || b.threshold_status === 'info').length}/${budgets.length} budgets on track`, icon: Shield, color: 'green' },
                { label: 'RI COVERAGE', value: `${stats.ri_coverage}%`, sub: `Target: ${stats.target_coverage}%`, icon: Target, color: stats.ri_coverage >= stats.target_coverage ? 'green' : 'yellow' },
                { label: 'AGENT SAVINGS', value: stats?.data_source === 'azure_live' ? fmt(stats.ai_savings || 0) : fmt(agents.reduce((sum: number, a: any) => sum + (a.savings_identified || 0), 0)), sub: stats?.data_source === 'azure_live' ? 'From Azure recommendations' : `${agents.length} agents active`, icon: Bot, color: 'purple' },
              ].map((s, i) => (
                <div key={i} className={`rounded-xl border p-5 bg-slate-900 border-slate-800`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 font-medium">{s.label}</span>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-${s.color}-500/20`}>
                      <s.icon className={`w-4 h-4 text-${s.color}-400`} />
                    </div>
                  </div>
                  <p className={`text-2xl font-bold text-${s.color}-400`}>{s.value}</p>
                  {s.change && <p className="text-xs mt-1 text-green-400">{s.change}</p>}
                  {s.sub && <p className="text-xs text-slate-500 mt-1">{s.sub}</p>}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-6">
              {/* Anomaly Resolution Timeline */}
              <div className="col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Activity className="w-5 h-5 text-orange-400" />
                  <h3 className="font-semibold text-white">Anomaly Resolution Timeline</h3>
                  {stats?.data_source === 'azure_live' && <span className="px-2 py-0.5 rounded text-xs bg-yellow-500/20 text-yellow-400">DEMO</span>}
                </div>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {alerts.slice(0, 8).map((alert: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg">
                      <div className={`w-2 h-2 rounded-full mt-2 ${alert.status === 'auto-resolved' ? 'bg-green-400' : alert.status === 'owner-notified' ? 'bg-blue-400' : alert.status === 'investigating' ? 'bg-yellow-400' : alert.status === 'dismissed' ? 'bg-slate-400' : 'bg-red-400'}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{alert.resource}</p>
                        <p className="text-xs text-slate-400">{alert.message}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-2 py-0.5 rounded text-xs ${alert.status === 'auto-resolved' ? 'bg-green-500/20 text-green-400' : alert.status === 'owner-notified' ? 'bg-blue-500/20 text-blue-400' : alert.status === 'investigating' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-500/20 text-slate-400'}`}>
                            {alert.status === 'auto-resolved' ? 'Resolved' : alert.status === 'owner-notified' ? 'Owner Notified' : alert.status === 'investigating' ? 'Investigating' : alert.status === 'dismissed' ? 'Dismissed' : 'Pending'}
                          </span>
                          <span className="text-xs text-slate-500">{alert.delta}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Budget Guardrails Status */}
              <div className="col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-5 h-5 text-blue-400" />
                  <h3 className="font-semibold text-white">Budget Guardrails</h3>
                  {stats?.data_source === 'azure_live' && <span className="px-2 py-0.5 rounded text-xs bg-yellow-500/20 text-yellow-400">DEMO</span>}
                </div>
                <div className="space-y-3">
                  {budgets.map((budget: any, i: number) => (
                    <div key={i} className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-white">{budget.name}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${budget.threshold_status === 'critical' ? 'bg-red-500/20 text-red-400' : budget.threshold_status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : budget.threshold_status === 'info' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'}`}>
                          {budget.percentage}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div className={`h-2 rounded-full ${budget.threshold_status === 'critical' ? 'bg-red-500' : budget.threshold_status === 'warning' ? 'bg-yellow-500' : budget.threshold_status === 'info' ? 'bg-blue-500' : 'bg-green-500'}`} style={{ width: `${Math.min(budget.percentage, 100)}%` }} />
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-xs text-slate-500">{fmt(budget.spent)} / {fmt(budget.budget)}</span>
                        <span className={`text-xs ${budget.threshold_status === 'critical' ? 'text-red-400' : budget.threshold_status === 'warning' ? 'text-yellow-400' : 'text-slate-500'}`}>
                          {budget.threshold_status === 'critical' ? '⚠️ Over 90%' : budget.threshold_status === 'warning' ? '⚠️ Over 80%' : budget.threshold_status === 'info' ? 'ℹ️ Over 60%' : '✓ On track'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Agent Performance */}
              <div className="col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Bot className="w-5 h-5 text-purple-400" />
                  <h3 className="font-semibold text-white">AI Agent Performance</h3>
                </div>
                <div className="space-y-3">
                  {agents.filter((a: any) => a.role === 'primary').slice(0, 5).map((agent: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${agent.color}20` }}>
                          <Brain className="w-4 h-4" style={{ color: agent.color }} />
                        </div>
                        <div>
                          <p className="text-sm text-white">{agent.name}</p>
                          <p className="text-xs text-slate-400">{agent.actions_today} actions today</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-green-400">{fmt(agent.savings_identified)}</p>
                        <p className="text-xs text-slate-500">{agent.accuracy}% accuracy</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* RI/SP Action Metrics */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Target className="w-5 h-5 text-cyan-400" />
                <h3 className="font-semibold text-white">RI/SP Recommendation Actions</h3>
              </div>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-2">
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  </div>
                  <p className="text-2xl font-bold text-green-400">{rispActions.approved_count}</p>
                  <p className="text-sm text-slate-400">Approved</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                  <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-2">
                    <Clock className="w-6 h-6 text-yellow-400" />
                  </div>
                  <p className="text-2xl font-bold text-yellow-400">{rispActions.held_count}</p>
                  <p className="text-sm text-slate-400">On Hold</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                  <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-2">
                    <X className="w-6 h-6 text-red-400" />
                  </div>
                  <p className="text-2xl font-bold text-red-400">{rispActions.blocked_count}</p>
                  <p className="text-sm text-slate-400">Blocked</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                  <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center mx-auto mb-2">
                    <DollarSign className="w-6 h-6 text-cyan-400" />
                  </div>
                  <p className="text-2xl font-bold text-cyan-400">{fmt(rispActions.total_approved_savings)}</p>
                  <p className="text-sm text-slate-400">Approved Savings</p>
                </div>
              </div>
              {rispActions.approved_count + rispActions.held_count + rispActions.blocked_count > 0 && (
                <div className="mt-4 p-3 bg-slate-800/30 rounded-lg">
                  <p className="text-sm text-slate-400">
                    <span className="text-white font-medium">{rispActions.approved_count + rispActions.held_count + rispActions.blocked_count}</span> total recommendations reviewed. 
                    <span className="text-green-400 ml-2">{rispActions.approved_count > 0 ? `${Math.round(rispActions.approved_count / (rispActions.approved_count + rispActions.held_count + rispActions.blocked_count) * 100)}% approval rate` : 'No approvals yet'}</span>
                  </p>
                </div>
              )}
            </div>

            {/* Conversational AI Section with Query Buttons on Left */}
            <div className="grid grid-cols-4 gap-6">
              {/* Left Panel - Query Buttons */}
              <div className="col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-4">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <h3 className="font-semibold text-white text-sm">Quick Queries</h3>
                </div>
                <div className="space-y-2">
                  {[
                    { label: "Last Month's Anomalies", query: "Show me last month's anomalies and how they were resolved", icon: AlertTriangle, color: "text-red-400" },
                    { label: "GPU Spike Analysis", query: "How was the GPU spike resolved?", icon: Activity, color: "text-orange-400" },
                    { label: "Budget Status", query: "What's our current budget status?", icon: Shield, color: "text-blue-400" },
                    { label: "RI Coverage Plan", query: "Explain RI coverage recommendations and savings", icon: Target, color: "text-green-400" },
                    { label: "SQL Recommendations", query: "Why 3-year RI for SQL workloads?", icon: Server, color: "text-purple-400" },
                    { label: "Cost Savings Summary", query: "What were our total savings this month?", icon: DollarSign, color: "text-emerald-400" },
                  ].map((item, i) => (
                    <button
                      key={i}
                      onClick={() => handleExecChat(item.query)}
                      className="w-full flex items-center gap-3 p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg transition-colors text-left group"
                    >
                      <item.icon className={`w-4 h-4 ${item.color} group-hover:scale-110 transition-transform`} />
                      <span className="text-sm text-slate-300 group-hover:text-white">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Right Panel - Chat Interface */}
              <div className="col-span-3 bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <MessageSquare className="w-5 h-5 text-purple-400" />
                    <h3 className="font-semibold text-white">Azure FinOps Copilot</h3>
                    <select 
                      value={selectedAgent}
                      onChange={(e) => setSelectedAgent(e.target.value)}
                      className="px-3 py-1 bg-slate-800 border border-slate-700 text-purple-400 text-xs rounded-lg focus:outline-none focus:border-purple-500"
                    >
                      {availableAgents.map(agent => (
                        <option key={agent.id} value={agent.id} disabled={!agent.connected}>
                          {agent.name} {!agent.connected && '(Not Connected)'}
                        </option>
                      ))}
                    </select>
                  </div>
                  {azureStatus.configured && (
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full flex items-center gap-2">
                      <CheckCircle className="w-3 h-3" /> Connected to Azure
                    </span>
                  )}
                </div>

                {/* Chat Messages */}
                <div className="bg-slate-800/50 rounded-lg p-4 h-72 overflow-y-auto mb-4 space-y-3">
                  {execChatMessages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-3xl px-4 py-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`}>
                        {msg.role === 'assistant' && <span className="text-xs text-purple-400 block mb-1">Azure FinOps Copilot</span>}
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Chat Input */}
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={execChatInput}
                    onChange={(e) => setExecChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleExecChat()}
                    placeholder="Ask about costs, anomalies, savings, budgets, or RI recommendations..."
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <button onClick={() => handleExecChat()} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2">
                    <Send className="w-4 h-4" /> Ask AI
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

                {activeTab === 'command' && stats && (
                  <div className="space-y-6">
                    {/* Phase 2: Anomaly Alert Banner */}
                    {detectedAnomalies.length > 0 && (
                      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5 text-red-400" />
                          <span className="text-red-400 font-medium">
                            {detectedAnomalies.length} cost anomal{detectedAnomalies.length > 1 ? 'ies' : 'y'} detected
                          </span>
                        </div>
                        <div className="mt-2 text-sm text-red-300">
                          {detectedAnomalies[0]?.date}: ${detectedAnomalies[0]?.actual?.toLocaleString()} 
                          ({detectedAnomalies[0]?.variance_pct > 0 ? '+' : ''}{detectedAnomalies[0]?.variance_pct}% vs baseline)
                        </div>
                      </div>
                    )}
                    <div className="grid grid-cols-6 gap-4">
              {[
                { label: 'MONTHLY SPEND', value: fmt(stats.monthly_spend), change: '-8.2%', icon: DollarSign },
                { label: 'AI SAVINGS', value: fmt(stats.ai_savings), change: '+15.3%', icon: Brain, highlight: true },
                { label: 'HIDDEN COSTS', value: fmt(stats.hidden_costs_found), sub: 'Mitigated', icon: Search },
                { label: 'RI COVERAGE', value: `${stats.ri_coverage}%`, sub: `Target: ${stats.target_coverage}%`, icon: Target },
                { label: 'BUDGET VARIANCE', value: `+${stats.budget_variance}%`, sub: 'In Control', icon: Shield },
                { label: 'FORECAST ACCURACY', value: `${stats.forecast_accuracy}%`, change: '+2.1%', icon: TrendingUp },
              ].map((s, i) => (
                <div key={i} className={`rounded-xl border p-5 ${s.highlight ? 'bg-gradient-to-br from-green-900/30 to-emerald-900/30 border-green-500/30' : 'bg-slate-900 border-slate-800'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 font-medium">{s.label}</span>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${s.highlight ? 'bg-green-500/20' : 'bg-slate-800'}`}>
                      <s.icon className={`w-4 h-4 ${s.highlight ? 'text-green-400' : 'text-slate-400'}`} />
                    </div>
                  </div>
                  <p className={`text-2xl font-bold ${s.highlight ? 'text-green-400' : 'text-white'}`}>{s.value}</p>
                  {s.change && <p className="text-xs mt-1 text-green-400">{s.change}</p>}
                  {s.sub && <p className="text-xs text-slate-500 mt-1">{s.sub}</p>}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3"><Activity className="w-5 h-5 text-red-400" /><h3 className="font-semibold text-white">Real-Time Anomaly Detection</h3></div>
                  {stats?.data_source === 'azure_live' ? (
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs font-medium rounded-full">Live Azure Data</span>
                  ) : (
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">ML Model Active</span>
                  )}
                </div>
                {stats?.data_source === 'azure_live' || anomalyData.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-[250px] text-slate-500">
                    <Activity className="w-12 h-12 mb-3 opacity-50" />
                    <p className="text-sm">No anomaly data available</p>
                    <p className="text-xs mt-1">Cost anomaly detection requires historical data</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <ComposedChart data={anomalyData}>
                      <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="100%" stopColor="#10b981" stopOpacity={0.05}/></linearGradient></defs>
                      <XAxis dataKey="date" stroke="#475569" fontSize={11} />
                      <YAxis stroke="#475569" fontSize={11} tickFormatter={(v) => `$${(v/1000).toFixed(1)}K`} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                      <Area type="monotone" dataKey="expected" stroke="none" fill="url(#ag)" />
                      <Line type="monotone" dataKey="expected" stroke="#10b981" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
                <div className="mt-4 space-y-2">
                    {alerts.slice(0, 2).map((a: any, i: number) => (
                      <div key={i} onClick={() => openAlertWorkflow(a)} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3 cursor-pointer hover:bg-slate-700/50 transition-colors">
                        <div className="flex items-center gap-3">
                          <AlertTriangle className={`w-4 h-4 ${a.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}`} />
                          <div><p className="text-sm text-white">{a.resource}: {a.delta}</p><p className="text-xs text-slate-400">{a.message}</p></div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${a.status === 'investigating' ? 'bg-yellow-500/20 text-yellow-400' : a.status === 'auto-resolved' ? 'bg-blue-500/20 text-blue-400' : a.status === 'dismissed' ? 'bg-slate-500/20 text-slate-400' : 'bg-green-500/20 text-green-400'}`}>{a.status}</span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4"><Bot className="w-5 h-5 text-purple-400" /><h3 className="font-semibold text-white">AI Agent Fleet</h3></div>
                <div className="space-y-3">
                  {agents.filter((a: any) => a.role === 'primary').slice(0, 4).map((agent: any) => (
                    <div key={agent.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${agent.color}20` }}>
                          <Shield className="w-4 h-4" style={{ color: agent.color }} />
                        </div>
                        <div><p className="text-sm font-medium text-white">{agent.name}</p><p className="text-xs text-slate-400 truncate max-w-28">{agent.last_action}</p></div>
                      </div>
                      <div className="text-right"><p className="text-sm font-bold text-green-400">${(agent.savings_identified || 0).toLocaleString()}</p><p className="text-xs text-slate-400">{agent.actions_today} actions</p></div>
                    </div>
                  ))}
                </div>
                <button onClick={() => setActiveTab('agents')} className="w-full mt-4 py-2 text-sm text-slate-400 hover:text-white border border-slate-700 rounded-lg hover:bg-slate-800">View All Agents</button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-6">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4"><Sparkles className="w-5 h-5 text-blue-400" /><h3 className="font-semibold text-white">6-Month Forecast</h3></div>
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={forecast}>
                    <defs><linearGradient id="fg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3}/><stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05}/></linearGradient></defs>
                    <XAxis dataKey="month" stroke="#475569" fontSize={10} />
                    <YAxis stroke="#475569" fontSize={10} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="predicted" stroke="#3b82f6" fill="url(#fg)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4"><Zap className="w-5 h-5 text-yellow-400" /><h3 className="font-semibold text-white">Quick Actions</h3></div>
                <div className="space-y-3">
                  <button onClick={fetchData} className="w-full flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 text-left"><RefreshCw className="w-4 h-4 text-slate-400" /><div><p className="text-sm font-medium text-white">Run Full Scan</p><p className="text-xs text-slate-400">Scan all resources</p></div></button>
                  <button onClick={generateDemoAlert} className="w-full flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 text-left"><Bell className="w-4 h-4 text-slate-400" /><div><p className="text-sm font-medium text-white">Generate Alert</p><p className="text-xs text-slate-400">Demo notification</p></div></button>
                  <button onClick={() => setActiveTab('risp')} className="w-full flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 text-left"><Target className="w-4 h-4 text-slate-400" /><div><p className="text-sm font-medium text-white">Purchase RIs</p><p className="text-xs text-slate-400">Review recommendations</p></div></button>
                </div>
              </div>

              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4"><Shield className="w-5 h-5 text-orange-400" /><h3 className="font-semibold text-white">Budget Health</h3></div>
                <div className="space-y-3">
                  {budgets.slice(0, 4).map((b: any) => (
                    <div key={b.id} className="space-y-1">
                      <div className="flex justify-between text-xs"><span className="text-slate-400">{b.name.replace(' Budget', '')}</span><span className="text-white">${(b.current/1000).toFixed(0)}K / ${(b.allocated/1000).toFixed(0)}K</span></div>
                      <div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className={`h-full rounded-full ${b.status === 'critical' ? 'bg-red-500' : b.status === 'warning' ? 'bg-orange-500' : 'bg-green-500'}`} style={{ width: `${Math.min(100, (b.current / b.allocated) * 100)}%` }} /></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-purple-400" />Primary Agents</h3>
              {agents.filter((a: any) => a.role === 'primary').map((agent: any) => (
                <div key={agent.id} className="bg-slate-900 rounded-xl border border-slate-800 p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${agent.color}20` }}><Bot className="w-6 h-6" style={{ color: agent.color }} /></div>
                      <div><h4 className="font-semibold text-white">{agent.name}</h4><p className="text-sm text-slate-400">{agent.type}</p><p className="text-xs text-slate-500 mt-1">{agent.azure_service}</p></div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /><span className="text-xs text-green-400">Active</span></div>
                      <p className="text-lg font-bold text-green-400 mt-1">{agent.accuracy}%</p><p className="text-xs text-slate-400">Accuracy</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <p className="text-sm text-slate-300">{agent.last_action}</p>
                    <div className="flex items-center justify-between mt-2"><span className="text-xs text-slate-400">{agent.actions_today} actions today</span>{agent.savings_identified && <span className="text-sm font-semibold text-green-400">${agent.savings_identified.toLocaleString()} identified</span>}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2"><CheckCircle className="w-5 h-5 text-cyan-400" />Validator Agents</h3>
              {agents.filter((a: any) => a.role === 'validator').map((agent: any) => (
                <div key={agent.id} className="bg-slate-900 rounded-xl border border-cyan-900/50 p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${agent.color}20` }}><CheckCircle className="w-6 h-6" style={{ color: agent.color }} /></div>
                      <div><h4 className="font-semibold text-white">{agent.name}</h4><p className="text-sm text-slate-400">{agent.type}</p><p className="text-xs text-cyan-400 mt-1">Validates: {agent.validates}</p></div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" /><span className="text-xs text-cyan-400">Validating</span></div>
                      <p className="text-lg font-bold text-cyan-400 mt-1">{agent.accuracy}%</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800"><p className="text-sm text-slate-300">{agent.last_action}</p></div>
                </div>
              ))}
              <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 rounded-xl border border-purple-500/30 p-5">
                <h4 className="font-semibold text-white mb-3">Agent Orchestration</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-400">Primary Agents</span><span className="text-green-400">{agents.filter((a: any) => a.role === 'primary').length} Active</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Validator Agents</span><span className="text-cyan-400">{agents.filter((a: any) => a.role === 'validator').length} Active</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Cross-Validation</span><span className="text-white">100%</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'hidden' && hiddenCosts && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 rounded-xl border border-yellow-500/30 p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-yellow-500/20 flex items-center justify-center"><Search className="w-7 h-7 text-yellow-400" /></div>
                  <div><h2 className="text-xl font-bold text-white">Hidden Cost Hunter Active</h2><p className="text-sm text-slate-400">AI agents continuously scanning for cost leaks</p></div>
                </div>
                <div className="flex items-center gap-8">
                  <div className="text-center"><p className="text-2xl font-bold text-white">${(hiddenCosts.total_detected/1000).toFixed(1)}K</p><p className="text-xs text-slate-400">Total Detected</p></div>
                  <div className="text-center"><p className="text-2xl font-bold text-green-400">${(hiddenCosts.total_mitigated/1000).toFixed(1)}K</p><p className="text-xs text-green-400">Total Mitigated</p></div>
                  <div className="text-center"><p className="text-2xl font-bold text-white">{hiddenCosts.recovery_rate}%</p><p className="text-xs text-slate-400">Recovery Rate</p></div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {hiddenCosts.categories.map((c: any) => (
                <div key={c.id} className="bg-slate-900 rounded-xl border border-slate-800 p-5">
                  <div className="flex items-center justify-between mb-3"><h4 className="font-semibold text-white">{c.name}</h4><span className={`px-2 py-1 rounded text-xs font-medium ${c.status === 'eliminated' ? 'bg-green-500/20 text-green-400' : c.status === 'controlled' ? 'bg-blue-500/20 text-blue-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{c.status}</span></div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">Detected</span><span className="text-red-400">${c.detected.toLocaleString()}/mo</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Mitigated</span><span className="text-green-400">${c.mitigated.toLocaleString()}/mo</span></div>
                    <div className="flex justify-between font-semibold"><span className="text-slate-400">Savings</span><span className="text-white">${c.monthly_savings.toLocaleString()}</span></div>
                  </div>
                  <div className="mt-3 h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full" style={{ width: `${c.progress}%` }} /></div>
                  <p className="text-xs text-slate-500 mt-2 flex items-center gap-1"><Bot className="w-3 h-3" /> {c.managed_by}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'budget' && (
          <div className="space-y-6">
            <div className="grid grid-cols-5 gap-4">
              {budgets.map((b: any) => (
                <div key={b.id} className={`bg-slate-900 rounded-xl border p-5 ${b.status === 'critical' ? 'border-red-500/50' : b.status === 'warning' ? 'border-yellow-500/50' : 'border-slate-800'}`}>
                  <div className="flex items-center justify-between mb-3"><h4 className="font-medium text-white text-sm">{b.name}</h4>{b.status === 'critical' ? <AlertTriangle className="w-4 h-4 text-red-400" /> : b.status === 'warning' ? <AlertTriangle className="w-4 h-4 text-yellow-400" /> : <CheckCircle className="w-4 h-4 text-green-400" />}</div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-3"><div className={`h-full rounded-full ${b.status === 'critical' ? 'bg-red-500' : b.status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${Math.min(100, (b.current / b.allocated) * 100)}%` }} /></div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between"><span className="text-slate-400">Current</span><span className="text-white">${(b.current/1000).toFixed(0)}K</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Allocated</span><span className="text-white">${(b.allocated/1000).toFixed(0)}K</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Forecast</span><span className={b.forecast > b.allocated ? 'text-red-400' : 'text-green-400'}>${(b.forecast/1000).toFixed(0)}K</span></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <h3 className="font-semibold text-white mb-4">Budget Alert Thresholds</h3>
              <div className="grid grid-cols-3 gap-4">
                {[{ t: '75%', s: 'Info', c: 'blue', d: 'Email notification to FinOps team' }, { t: '90%', s: 'Warning', c: 'yellow', d: 'Email + Slack to IT leadership' }, { t: '100%', s: 'Critical', c: 'red', d: 'All channels + PagerDuty escalation' }].map((a, i) => (
                  <div key={i} className={`bg-${a.c}-900/20 border border-${a.c}-500/30 rounded-xl p-5`} style={{ backgroundColor: a.c === 'blue' ? 'rgba(59,130,246,0.1)' : a.c === 'yellow' ? 'rgba(234,179,8,0.1)' : 'rgba(239,68,68,0.1)', borderColor: a.c === 'blue' ? 'rgba(59,130,246,0.3)' : a.c === 'yellow' ? 'rgba(234,179,8,0.3)' : 'rgba(239,68,68,0.3)' }}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: a.c === 'blue' ? 'rgba(59,130,246,0.2)' : a.c === 'yellow' ? 'rgba(234,179,8,0.2)' : 'rgba(239,68,68,0.2)' }}><Bell className="w-5 h-5" style={{ color: a.c === 'blue' ? '#60a5fa' : a.c === 'yellow' ? '#facc15' : '#f87171' }} /></div>
                      <div><p className="font-semibold text-white">{a.t} Threshold</p><p className="text-xs" style={{ color: a.c === 'blue' ? '#60a5fa' : a.c === 'yellow' ? '#facc15' : '#f87171' }}>{a.s} Alert</p></div>
                    </div>
                    <p className="text-sm text-slate-400">{a.d}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <h3 className="font-semibold text-white mb-4">Daily Variance Monitoring</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={varianceData}>
                  <XAxis dataKey="day" stroke="#475569" fontSize={11} />
                  <YAxis stroke="#475569" fontSize={11} tickFormatter={(v) => `${v}%`} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                  <Bar dataKey="variance" radius={[4, 4, 0, 0]}>{varianceData.map((e: any, i: number) => <Cell key={i} fill={Math.abs(e.variance) > 15 ? '#ef4444' : Math.abs(e.variance) > 10 ? '#f59e0b' : '#10b981'} />)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'risp' && (
          <div className="space-y-6">
            <div className="grid grid-cols-5 gap-4">
              {[
                { l: 'CURRENT RI COVERAGE', v: `${stats?.ri_coverage || 35}%`, c: 'green' },
                { l: 'CURRENT SP COVERAGE', v: `${stats?.sp_coverage || 25}%`, c: 'purple' },
                { l: 'TARGET COVERAGE', v: `${stats?.target_coverage || 60}%`, c: 'white' },
                { l: 'POTENTIAL SAVINGS', v: '$89K', c: 'green' },
                { l: 'ACTIVE EVALUATIONS', v: `${evaluations.length}`, c: 'yellow' }
              ].map((s, i) => (
                <div key={i} className="bg-slate-900 rounded-xl border border-slate-800 p-5">
                  <p className="text-xs text-slate-400 mb-1">{s.l}</p>
                  <p className={`text-3xl font-bold ${s.c === 'green' ? 'text-green-400' : s.c === 'purple' ? 'text-purple-400' : s.c === 'yellow' ? 'text-yellow-400' : 'text-white'}`}>{s.v}</p>
                </div>
              ))}
            </div>

            {/* SaaS Evaluations Section */}
            <div className="bg-slate-900 rounded-xl border border-amber-500/30 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <h3 className="font-semibold text-white">Upcoming SaaS / Technology Evaluations</h3>
                  <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded">Affects RI/SP Decisions</span>
                </div>
              </div>
              <p className="text-sm text-slate-400 mb-4">Track technology evaluations that may replace Azure workloads. Agents will automatically HOLD commitments for affected resources until decisions are made.</p>
              
              {evaluations.length > 0 ? (
                <table className="w-full mb-4">
                  <thead><tr className="text-left text-xs text-slate-400 border-b border-slate-800"><th className="pb-3">Evaluation</th><th className="pb-3">Vendor</th><th className="pb-3">Workload</th><th className="pb-3">Status</th><th className="pb-3">Decision Date</th><th className="pb-3">Adoption Risk</th><th className="pb-3">Holding</th><th className="pb-3">Actions</th></tr></thead>
                  <tbody>
                    {evaluations.map((e: any) => (
                      <tr key={e.id} className="border-b border-slate-800/50 text-sm">
                        <td className="py-3 font-medium text-white">{e.name}</td>
                        <td className="py-3 text-slate-400">{e.vendor}</td>
                        <td className="py-3 text-slate-400">{workloads.find((w: any) => w.id === e.workload_id)?.name || 'Unknown'}</td>
                        <td className="py-3"><span className={`px-2 py-1 rounded text-xs ${e.status === 'poc' ? 'bg-blue-500/20 text-blue-400' : e.status === 'pilot' ? 'bg-purple-500/20 text-purple-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{e.status?.toUpperCase()}</span></td>
                        <td className="py-3 text-slate-400">{e.decision_date || 'TBD'}</td>
                        <td className="py-3"><span className={`px-2 py-1 rounded text-xs ${e.adoption_probability_pct >= 70 ? 'bg-red-500/20 text-red-400' : e.adoption_probability_pct >= 40 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>{e.adoption_probability_pct}%</span></td>
                        <td className="py-3">{e.hold_commitments ? <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded">HOLDING</span> : <span className="text-slate-500 text-xs">No</span>}</td>
                        <td className="py-3"><button onClick={() => deleteEvaluation(e.id)} className="text-red-400 hover:text-red-300 text-xs">Delete</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-6 text-slate-500 mb-4">No active evaluations. Add one below to track SaaS decisions that affect RI/SP commitments.</div>
              )}

              {/* Add Evaluation Form */}
              <div className="bg-slate-800/50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-white mb-3">Add New Evaluation</h4>
                <div className="grid grid-cols-6 gap-3">
                  <input type="text" placeholder="Evaluation name (e.g., Snowflake POC)" value={newEvaluation.name} onChange={e => setNewEvaluation(prev => ({ ...prev, name: e.target.value }))} className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white" />
                  <input type="text" placeholder="Vendor" value={newEvaluation.vendor} onChange={e => setNewEvaluation(prev => ({ ...prev, vendor: e.target.value }))} className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white" />
                                    <select value={newEvaluation.workload_id} onChange={async (e) => {
                                        const val = e.target.value
                                        if (val.startsWith('new:')) {
                                          // Create new workload from resource
                                          const resourceName = val.replace('new:', '')
                                          const rec = recommendations.find((r: any) => r.resource === resourceName)
                                          try {
                                            const res = await fetch(`${API_URL}/api/workloads`, {
                                              method: 'POST',
                                              headers: { 'Content-Type': 'application/json' },
                                              body: JSON.stringify({
                                                name: resourceName,
                                                description: `Workload for ${rec?.type || 'resource'} - ${resourceName}`,
                                                criticality: rec?.stability >= 95 ? 'high' : rec?.stability >= 85 ? 'medium' : 'low',
                                                owner: 'FinOps Team',
                                                azure_services: [rec?.type || 'Virtual Machines'],
                                                monthly_cost: rec?.ea_price || rec?.monthly_cost || 0
                                              })
                                            })
                                            const data = await res.json()
                                            if (data.id) {
                                              toast.success(`Workload "${resourceName}" created`)
                                              await fetchData()
                                              setNewEvaluation(prev => ({ ...prev, workload_id: data.id }))
                                            }
                                          } catch (err) {
                                            toast.error('Failed to create workload')
                                          }
                                        } else {
                                          setNewEvaluation(prev => ({ ...prev, workload_id: val }))
                                        }
                                      }} className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white">
                                      <option value="">Select Workload or Resource</option>
                                      {workloads.length > 0 && <optgroup label="Registered Workloads">
                                        {workloads.map((w: any) => <option key={w.id} value={w.id}>{w.name}</option>)}
                                      </optgroup>}
                                      <optgroup label="Create from Resource">
                                        {recommendations.filter((r: any) => !workloads.some((w: any) => w.name === r.resource)).map((r: any, i: number) => (
                                          <option key={`new-${i}`} value={`new:${r.resource}`}>{r.resource} ({r.type})</option>
                                        ))}
                                      </optgroup>
                                    </select>
                  <input type="date" placeholder="Decision Date" value={newEvaluation.decision_date} onChange={e => setNewEvaluation(prev => ({ ...prev, decision_date: e.target.value }))} className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white" />
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Adoption:</span>
                    <input type="range" min="0" max="100" value={newEvaluation.adoption_probability} onChange={e => setNewEvaluation(prev => ({ ...prev, adoption_probability: parseInt(e.target.value) }))} className="flex-1" />
                    <span className="text-xs text-white w-8">{newEvaluation.adoption_probability}%</span>
                  </div>
                  <button onClick={createEvaluation} className="bg-amber-500 hover:bg-amber-600 text-black font-medium rounded px-4 py-2 text-sm">Add Evaluation</button>
                </div>
              </div>
            </div>

            {/* AI-Powered Recommendations with Workload Intelligence */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3"><Sparkles className="w-5 h-5 text-purple-400" /><h3 className="font-semibold text-white">AI-Powered Commitment Recommendations</h3></div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${dataSource === 'azure' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{dataSource === 'azure' ? 'LIVE DATA' : 'DEMO DATA'}</span>
                  <span className="px-3 py-1 bg-purple-500/20 text-purple-400 text-xs font-medium rounded-full">Multi-Agent Ensemble (GPT-5, O3, O4-Mini, GPT-4.1)</span>
                </div>
              </div>
              <p className="text-sm text-slate-400 mb-4">Click any row to open the deep-dive drawer with AI analysis, workload context, and override options.</p>
                            <table className="w-full">
                              <thead><tr className="text-left text-xs text-slate-400 border-b border-slate-800"><th className="pb-3">Resource</th><th className="pb-3">Workload</th><th className="pb-3">Type</th><th className="pb-3">Monthly Cost</th><th className="pb-3">Risk</th><th className="pb-3">AI Action</th><th className="pb-3">Reason</th><th className="pb-3">Re-evaluate By</th><th className="pb-3">Your Decision</th></tr></thead>
                              <tbody>
                                {(getAllSmartRecs().length > 0 ? getAllSmartRecs() : recommendations).map((r: any, i: number) => (
                                  <tr key={i} className="border-b border-slate-800/50 text-sm hover:bg-slate-800/40">
                                    <td className="py-4 font-medium text-white cursor-pointer" onClick={() => openRecommendationDrawer(r)}>{r.resource || r.sku || r.resource_id?.split('/').pop() || 'Resource'}</td>
                                    <td className="py-4">{(() => {
                                      const matchedWorkload = workloads.find((w: any) => w.name === r.resource || r.workload?.name === w.name)
                                      return matchedWorkload ? <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">{matchedWorkload.name}</span> : r.workload?.name ? <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">{r.workload.name}</span> : <span className="text-slate-500 text-xs">Unassigned</span>
                                    })()}</td>
                                    <td className="py-4 text-slate-400">{r.type || r.recommendation_type || 'RI'}</td>
                                    <td className="py-4 text-white">${(r.monthly_cost || r.net_savings || 0).toLocaleString()}</td>
                                    <td className="py-4">
                                      {r.intelligence?.risk_score !== undefined || r.agent_analysis?.risk_score !== undefined ? (
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${(r.intelligence?.risk_score || r.agent_analysis?.risk_score || 0) <= 3 ? 'bg-green-500/20 text-green-400' : (r.intelligence?.risk_score || r.agent_analysis?.risk_score || 0) <= 6 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                                          {(r.intelligence?.risk_score || r.agent_analysis?.risk_score || 0).toFixed(1)}/10
                                        </span>
                                      ) : <span className="text-slate-500 text-xs">-</span>}
                                    </td>
                                    <td className="py-4">
                                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        (r._action || r.intelligence?.action) === 'approve' ? 'bg-green-500/20 text-green-400' :
                                        (r._action || r.intelligence?.action) === 'modify' ? 'bg-blue-500/20 text-blue-400' :
                                        (r._action || r.intelligence?.action) === 'hold' ? 'bg-yellow-500/20 text-yellow-400' :
                                        (r._action || r.intelligence?.action) === 'block' ? 'bg-red-500/20 text-red-400' :
                                        'bg-green-500/20 text-green-400'
                                      }`}>
                                        {(r._action || r.intelligence?.action || r.recommendation || 'APPROVE').toUpperCase()}
                                      </span>
                                    </td>
                                    <td className="py-4 text-slate-400 text-xs max-w-xs truncate">{r.intelligence?.reason || r.intelligence?.evaluation_name || '-'}</td>
                                    <td className="py-4">{r.evaluation?.decision_date || r.intelligence?.decision_date ? <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded">{r.evaluation?.decision_date || r.intelligence?.decision_date}</span> : <span className="text-slate-500 text-xs">-</span>}</td>
                                    <td className="py-4">
                                      <div className="flex items-center gap-1">
                                        <button onClick={(e) => { e.stopPropagation(); recordRispAction('approve', r) }} className="px-2 py-1 bg-green-500/20 hover:bg-green-500/40 text-green-400 text-xs rounded transition-colors" title="Approve this recommendation">Approve</button>
                                        <button onClick={(e) => { e.stopPropagation(); recordRispAction('hold', r) }} className="px-2 py-1 bg-yellow-500/20 hover:bg-yellow-500/40 text-yellow-400 text-xs rounded transition-colors" title="Put on hold">Hold</button>
                                        <button onClick={(e) => { e.stopPropagation(); recordRispAction('block', r) }} className="px-2 py-1 bg-red-500/20 hover:bg-red-500/40 text-red-400 text-xs rounded transition-colors" title="Block this recommendation">Block</button>
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
            </div>

            {/* Workload Registry */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-5 h-5 text-blue-400" />
                <h3 className="font-semibold text-white">Workload Registry</h3>
                <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">{workloads.length} Workloads</span>
              </div>
              <p className="text-sm text-slate-400 mb-4">Business applications mapped to Azure resources. Add context like "PACS - Picture Archiving System" to help AI agents make better commitment decisions.</p>
              {workloads.length > 0 ? (
                <div className="grid grid-cols-3 gap-4">
                  {workloads.map((w: any) => (
                    <div key={w.id} className="bg-slate-800/50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-white">{w.name}</h4>
                        <span className={`px-2 py-1 rounded text-xs ${w.status === 'active' ? 'bg-green-500/20 text-green-400' : w.status === 'evaluating' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-500/20 text-slate-400'}`}>{w.status?.toUpperCase()}</span>
                      </div>
                      <p className="text-sm text-slate-400 mb-2">{w.description || 'No description'}</p>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>Owner: {w.owner_name || 'Unassigned'}</span>
                        <span>Criticality: {w.criticality || 'standard'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500">No workloads registered. Workloads are created when you import Azure data or add them via the API.</div>
              )}
            </div>

            {/* RI vs SP Guidance */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-green-900/20 border border-green-500/30 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4"><Lock className="w-5 h-5 text-green-400" /><h4 className="font-semibold text-green-400">Choose Reserved Instances When:</h4></div>
                <ul className="space-y-2 text-sm text-slate-300">
                  {['Workload stability >90% over 6+ months', 'Single VM family with no expected changes', 'Maximum savings priority (up to 56% off)', 'Mission-critical apps that won\'t migrate'].map((t, i) => <li key={i} className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" />{t}</li>)}
                </ul>
                <div className="mt-4 p-3 bg-green-900/30 rounded-lg"><p className="text-sm text-green-400 font-medium">3-Year RI: Up to 56% savings</p><p className="text-sm text-green-400">1-Year RI: Up to 36% savings</p></div>
              </div>
              <div className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4"><Layers className="w-5 h-5 text-purple-400" /><h4 className="font-semibold text-purple-400">Choose Savings Plans When:</h4></div>
                <ul className="space-y-2 text-sm text-slate-300">
                  {['Workloads growing or changing', 'Multi-service usage (VMs, AKS, Functions)', 'Need flexibility to change VM families/regions', 'AI/ML workloads with evolving GPU needs'].map((t, i) => <li key={i} className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-purple-400" />{t}</li>)}
                </ul>
                <div className="mt-4 p-3 bg-purple-900/30 rounded-lg"><p className="text-sm text-purple-400 font-medium">3-Year SP: Up to 52% savings</p><p className="text-sm text-purple-400">1-Year SP: Up to 33% savings</p></div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'controls' && (
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-6"><Sliders className="w-5 h-5 text-blue-400" /><h3 className="font-semibold text-white">Automation Controls</h3></div>
              <div className="space-y-4">
                {controls.map((c: any) => (
                  <div key={c.id} className="flex items-center justify-between bg-slate-800/50 rounded-xl p-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${c.enabled ? 'bg-green-500/20' : 'bg-slate-700'}`}><Power className={`w-5 h-5 ${c.enabled ? 'text-green-400' : 'text-slate-500'}`} /></div>
                      <div><p className="font-medium text-white">{c.name}</p><p className="text-xs text-slate-400">{c.description}</p></div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${c.risk === 'low' ? 'bg-green-500/20 text-green-400' : c.risk === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>{c.risk} risk</span>
                      <div className={`w-12 h-6 rounded-full p-1 ${c.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${c.enabled ? 'translate-x-6' : ''}`} /></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-6"><Bell className="w-5 h-5 text-orange-400" /><h3 className="font-semibold text-white">Alert Configuration</h3></div>
              <div className="space-y-3">
                {alertConfigs.map((c: any) => (
                  <div key={c.id} className="flex items-center justify-between bg-slate-800/50 rounded-xl p-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${c.severity === 'critical' ? 'bg-red-400' : c.severity === 'warning' ? 'bg-yellow-400' : 'bg-blue-400'}`} />
                      <div><p className="font-medium text-white">{c.name}</p><p className="text-xs text-slate-400">{c.channels}</p></div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${c.severity === 'critical' ? 'bg-red-500/20 text-red-400' : c.severity === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'}`}>{c.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'mission' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-xl border border-purple-500/30 p-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-purple-500/20 flex items-center justify-center"><Brain className="w-7 h-7 text-purple-400" /></div>
                <div><h2 className="text-xl font-bold text-white">Mission Critical Workload Protection</h2><p className="text-sm text-slate-400">Healthcare systems with guaranteed uptime and cost predictability</p></div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {missionCritical.map((mc: any) => (
                <div key={mc.id} className="bg-slate-900 rounded-xl border border-slate-800 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3"><Shield className="w-5 h-5 text-green-400" /><h4 className="font-semibold text-white">{mc.name}</h4></div>
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded">{mc.status}</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">Monthly Cost</span><span className="text-white font-medium">${mc.monthly_cost.toLocaleString()}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Protection Level</span><span className="text-green-400">{mc.protection_level}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Coverage Type</span><span className="text-blue-400">{mc.coverage_type}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Capacity Headroom</span><span className="text-white">{mc.capacity_headroom}%</span></div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800"><div className="flex items-center gap-2 text-xs text-slate-400"><Lock className="w-3 h-3" /><span>Capacity reserved - Cost locked - SLA protected</span></div></div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-6"><Key className="w-5 h-5 text-blue-400" /><h3 className="font-semibold text-white">Azure Connection</h3></div>
                {azureStatus?.configured ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <div><p className="text-sm font-medium text-green-400">Connected to Azure</p><p className="text-xs text-slate-400">{azureStatus.tenant_name || 'Tenant configured'}</p></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="text-slate-400">Tenant ID:</span><span className="ml-2 text-white">{azureStatus.tenant_id}</span></div>
                      <div><span className="text-slate-400">Client ID:</span><span className="ml-2 text-white">{azureStatus.client_id}</span></div>
                      <div><span className="text-slate-400">Subscription:</span><span className="ml-2 text-white">{azureStatus.subscription_id}</span></div>
                      <div><span className="text-slate-400">Last Discovery:</span><span className="ml-2 text-white">{azureStatus.last_discovery ? new Date(azureStatus.last_discovery).toLocaleString() : 'Never'}</span></div>
                    </div>
                    <button onClick={runDiscovery} disabled={isDiscovering} className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium disabled:opacity-50">
                      {isDiscovering ? <><Loader2 className="w-4 h-4 animate-spin" />Running Discovery...</> : <><Play className="w-4 h-4" />Run Discovery</>}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-3">
                      <div><label className="text-xs text-slate-400 block mb-1">Tenant ID</label><input type="text" value={azureConfig.tenant_id} onChange={(e) => setAzureConfig({...azureConfig, tenant_id: e.target.value})} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500" /></div>
                      <div><label className="text-xs text-slate-400 block mb-1">Client ID (App Registration)</label><input type="text" value={azureConfig.client_id} onChange={(e) => setAzureConfig({...azureConfig, client_id: e.target.value})} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500" /></div>
                      <div><label className="text-xs text-slate-400 block mb-1">Client Secret</label><input type="password" value={azureConfig.client_secret} onChange={(e) => setAzureConfig({...azureConfig, client_secret: e.target.value})} placeholder="Enter client secret" className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500" /></div>
                      <div><label className="text-xs text-slate-400 block mb-1">Subscription ID</label><input type="text" value={azureConfig.subscription_id} onChange={(e) => setAzureConfig({...azureConfig, subscription_id: e.target.value})} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500" /></div>
                    </div>
                    <button onClick={saveAzureConfig} disabled={isConnecting} className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium disabled:opacity-50">
                      {isConnecting ? <><Loader2 className="w-4 h-4 animate-spin" />Connecting...</> : <><Save className="w-4 h-4" />Connect to Azure</>}
                    </button>
                  </div>
                )}
              </div>

              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-6"><Globe className="w-5 h-5 text-purple-400" /><h3 className="font-semibold text-white">Discovery Results</h3></div>
                {discoveryResult ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(discoveryResult.summary).filter(([k]) => k !== 'total').map(([key, value]) => (
                        <div key={key} className="bg-slate-800/50 rounded-lg p-3"><p className="text-xs text-slate-400 capitalize">{key.replace('_', ' ')}</p><p className="text-xl font-bold text-white">{String(value)}</p></div>
                      ))}
                    </div>
                    <div className="border-t border-slate-800 pt-4">
                      <div className="flex justify-between text-sm"><span className="text-slate-400">Total Resources</span><span className="text-white font-bold">{discoveryResult.summary.total}</span></div>
                      <div className="flex justify-between text-sm mt-2"><span className="text-slate-400">Monthly Spend</span><span className="text-white font-bold">${(discoveryResult.cost_summary.monthly_spend/1000).toFixed(0)}K</span></div>
                      <div className="flex justify-between text-sm mt-2"><span className="text-slate-400">Potential Savings</span><span className="text-green-400 font-bold">${(discoveryResult.cost_summary.potential_savings/1000).toFixed(0)}K</span></div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-48 text-slate-500">
                    <Server className="w-12 h-12 mb-3 opacity-50" />
                    <p className="text-sm">No discovery results yet</p>
                    <p className="text-xs mt-1">Connect to Azure and run discovery</p>
                  </div>
                )}
              </div>
            </div>

            {/* Manual Data Import Section */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <Layers className="w-5 h-5 text-cyan-400" />
                <h3 className="font-semibold text-white">Manual Data Import</h3>
                <div className="group relative">
                  <span className="text-slate-400 cursor-help text-sm">(How to export from Azure)</span>
                  <div className="absolute left-0 top-6 w-80 bg-slate-800 border border-slate-700 rounded-lg p-4 text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
                    <p className="font-semibold text-white mb-2">Export from Azure Portal:</p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Go to Azure Portal &gt; Advisor</li>
                      <li>Click "Cost" recommendations</li>
                      <li>Click "Download as CSV"</li>
                      <li>Paste the CSV content below</li>
                    </ol>
                    <p className="mt-2 text-slate-400">Supports: RI/SP recommendations, Cost data</p>
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-400 mb-4">Paste Azure Advisor CSV export to import RI/SP recommendations when live API access is blocked by Conditional Access.</p>
              <textarea 
                value={csvInput}
                onChange={(e) => setCsvInput(e.target.value)}
                placeholder={`Paste Azure Advisor CSV here...\n\nExample format:\n"Business Impact","Recommendation","Subscription ID",...\n"High","Consider purchasing a savings plan for compute",...`}
                className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 font-mono resize-none"
              />
              <div className="flex items-center gap-4 mt-4">
                <button 
                  onClick={importCsvData} 
                  disabled={isImporting || !csvInput.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isImporting ? <><Loader2 className="w-4 h-4 animate-spin" />Importing...</> : <><Layers className="w-4 h-4" />Import CSV Data</>}
                </button>
                {importStatus && (
                  <div className="flex items-center gap-2 text-sm text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span>Imported {importStatus.imported?.ri_recommendations || 0} recommendations at {new Date(importStatus.imported_at).toLocaleTimeString()}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-6"><Sliders className="w-5 h-5 text-orange-400" /><h3 className="font-semibold text-white">Automation Controls</h3></div>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(controlSettings).map(([id, settings]: [string, any]) => (
                  <div key={id} className="flex items-center justify-between bg-slate-800/50 rounded-xl p-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${settings.enabled ? 'bg-green-500/20' : 'bg-slate-700'}`}><Power className={`w-5 h-5 ${settings.enabled ? 'text-green-400' : 'text-slate-500'}`} /></div>
                      <div><p className="font-medium text-white capitalize">{id.replace(/-/g, ' ')}</p><p className="text-xs text-slate-400">{settings.schedule || settings.threshold_percent ? `Threshold: ${settings.threshold_percent || settings.schedule}` : 'Configurable'}</p></div>
                    </div>
                    <button onClick={() => toggleControl(id)} className={`w-12 h-6 rounded-full p-1 transition-colors ${settings.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${settings.enabled ? 'translate-x-6' : ''}`} /></button>
                  </div>
                ))}
              </div>
            </div>

                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                      <div className="flex items-center gap-3 mb-6"><Zap className="w-5 h-5 text-red-400" /><h3 className="font-semibold text-white">Circuit Breaker Thresholds</h3></div>
                      <div className="grid grid-cols-5 gap-4">
                        {Object.entries(circuitBreakers).map(([id, settings]: [string, any]) => (
                          <div key={id} className="bg-slate-800/50 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-3">
                              <p className="text-sm font-medium text-white capitalize">{id.replace(/-/g, ' ')}</p>
                              <span className={`w-2 h-2 rounded-full ${settings.enabled ? 'bg-green-400' : 'bg-red-400'}`} />
                            </div>
                            <div className="space-y-2">
                              <input type="number" value={settings.threshold} onChange={(e) => updateCircuitBreaker(id, Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                              <p className="text-xs text-slate-500">{settings.unit}</p>
                              <p className="text-xs text-blue-400">Action: {settings.action}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Alert Configuration with Sliders and Toggles */}
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                      <div className="flex items-center gap-3 mb-6"><Bell className="w-5 h-5 text-yellow-400" /><h3 className="font-semibold text-white">Alert Configuration</h3></div>
                      <div className="space-y-6">
                        {/* Anomaly Detection Alerts */}
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <AlertTriangle className="w-5 h-5 text-orange-400" />
                              <div><p className="font-medium text-white">Anomaly Detection</p><p className="text-xs text-slate-400">Alert when cost variance exceeds threshold</p></div>
                            </div>
                            <button onClick={() => setAlertSettings(prev => ({...prev, anomaly: {...prev.anomaly, enabled: !prev.anomaly.enabled}}))} className={`w-12 h-6 rounded-full p-1 transition-colors ${alertSettings.anomaly.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${alertSettings.anomaly.enabled ? 'translate-x-6' : ''}`} /></button>
                          </div>
                          {alertSettings.anomaly.enabled && (
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm"><span className="text-slate-400">Variance Threshold</span><span className="text-white font-medium">{alertSettings.anomaly.threshold}%</span></div>
                              <input type="range" min="5" max="50" value={alertSettings.anomaly.threshold} onChange={(e) => setAlertSettings(prev => ({...prev, anomaly: {...prev.anomaly, threshold: Number(e.target.value)}}))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-orange-500" />
                              <div className="flex justify-between text-xs text-slate-500"><span>5%</span><span>50%</span></div>
                            </div>
                          )}
                        </div>

                        {/* Budget Alerts */}
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <DollarSign className="w-5 h-5 text-green-400" />
                              <div><p className="font-medium text-white">Budget Alerts</p><p className="text-xs text-slate-400">Alert when budget utilization reaches thresholds</p></div>
                            </div>
                            <button onClick={() => setAlertSettings(prev => ({...prev, budget: {...prev.budget, enabled: !prev.budget.enabled}}))} className={`w-12 h-6 rounded-full p-1 transition-colors ${alertSettings.budget.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${alertSettings.budget.enabled ? 'translate-x-6' : ''}`} /></button>
                          </div>
                          {alertSettings.budget.enabled && (
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <div className="flex items-center justify-between text-sm"><span className="text-yellow-400">Warning Threshold</span><span className="text-white font-medium">{alertSettings.budget.warningThreshold}%</span></div>
                                <input type="range" min="50" max="95" value={alertSettings.budget.warningThreshold} onChange={(e) => setAlertSettings(prev => ({...prev, budget: {...prev.budget, warningThreshold: Number(e.target.value)}}))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-yellow-500" />
                              </div>
                              <div className="space-y-2">
                                <div className="flex items-center justify-between text-sm"><span className="text-red-400">Critical Threshold</span><span className="text-white font-medium">{alertSettings.budget.criticalThreshold}%</span></div>
                                <input type="range" min="60" max="100" value={alertSettings.budget.criticalThreshold} onChange={(e) => setAlertSettings(prev => ({...prev, budget: {...prev.budget, criticalThreshold: Number(e.target.value)}}))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-500" />
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Circuit Breaker Alerts */}
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <Zap className="w-5 h-5 text-red-400" />
                              <div><p className="font-medium text-white">Circuit Breaker Alerts</p><p className="text-xs text-slate-400">Alert when cost rate triggers circuit breaker</p></div>
                            </div>
                            <button onClick={() => setAlertSettings(prev => ({...prev, circuitBreaker: {...prev.circuitBreaker, enabled: !prev.circuitBreaker.enabled}}))} className={`w-12 h-6 rounded-full p-1 transition-colors ${alertSettings.circuitBreaker.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${alertSettings.circuitBreaker.enabled ? 'translate-x-6' : ''}`} /></button>
                          </div>
                          {alertSettings.circuitBreaker.enabled && (
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm"><span className="text-slate-400">Cost Rate Threshold</span><span className="text-white font-medium">${alertSettings.circuitBreaker.threshold}/hr</span></div>
                              <input type="range" min="100" max="2000" step="50" value={alertSettings.circuitBreaker.threshold} onChange={(e) => setAlertSettings(prev => ({...prev, circuitBreaker: {...prev.circuitBreaker, threshold: Number(e.target.value)}}))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-500" />
                              <div className="flex justify-between text-xs text-slate-500"><span>$100/hr</span><span>$2,000/hr</span></div>
                            </div>
                          )}
                        </div>

                        {/* Cost Spike Alerts */}
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <TrendingUp className="w-5 h-5 text-purple-400" />
                              <div><p className="font-medium text-white">Cost Spike Alerts</p><p className="text-xs text-slate-400">Alert on sudden cost increases</p></div>
                            </div>
                            <button onClick={() => setAlertSettings(prev => ({...prev, costSpike: {...prev.costSpike, enabled: !prev.costSpike.enabled}}))} className={`w-12 h-6 rounded-full p-1 transition-colors ${alertSettings.costSpike.enabled ? 'bg-green-500' : 'bg-slate-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-transform ${alertSettings.costSpike.enabled ? 'translate-x-6' : ''}`} /></button>
                          </div>
                          {alertSettings.costSpike.enabled && (
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm"><span className="text-slate-400">Spike Threshold</span><span className="text-white font-medium">{alertSettings.costSpike.threshold}% increase</span></div>
                              <input type="range" min="10" max="100" value={alertSettings.costSpike.threshold} onChange={(e) => setAlertSettings(prev => ({...prev, costSpike: {...prev.costSpike, threshold: Number(e.target.value)}}))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500" />
                              <div className="flex justify-between text-xs text-slate-500"><span>10%</span><span>100%</span></div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Discount Settings for RI/SP Pricing */}
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                      <div className="flex items-center gap-3 mb-6"><DollarSign className="w-5 h-5 text-green-400" /><h3 className="font-semibold text-white">RI/SP Discount Settings</h3></div>
                      <p className="text-sm text-slate-400 mb-4">Configure discount percentages for EA, Reserved Instances, and Savings Plans. Changes will recalculate all pricing in the RI/SP Optimizer.</p>
                      <div className="grid grid-cols-5 gap-4 mb-4">
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <p className="text-sm font-medium text-white mb-2">EA Discount</p>
                          <div className="flex items-center gap-2">
                            <input type="number" min="0" max="50" value={discountSettings.ea_discount} onChange={(e) => setDiscountSettings(prev => ({...prev, ea_discount: Number(e.target.value)}))} className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                            <span className="text-slate-400">%</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">Off list price</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <p className="text-sm font-medium text-white mb-2">RI 1-Year</p>
                          <div className="flex items-center gap-2">
                            <input type="number" min="0" max="80" value={discountSettings.ri_1year_discount} onChange={(e) => setDiscountSettings(prev => ({...prev, ri_1year_discount: Number(e.target.value)}))} className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                            <span className="text-slate-400">%</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">Off EA price</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <p className="text-sm font-medium text-white mb-2">RI 3-Year</p>
                          <div className="flex items-center gap-2">
                            <input type="number" min="0" max="80" value={discountSettings.ri_3year_discount} onChange={(e) => setDiscountSettings(prev => ({...prev, ri_3year_discount: Number(e.target.value)}))} className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                            <span className="text-slate-400">%</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">Off EA price</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <p className="text-sm font-medium text-white mb-2">SP 1-Year</p>
                          <div className="flex items-center gap-2">
                            <input type="number" min="0" max="80" value={discountSettings.sp_1year_discount} onChange={(e) => setDiscountSettings(prev => ({...prev, sp_1year_discount: Number(e.target.value)}))} className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                            <span className="text-slate-400">%</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">Off EA price</p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-4">
                          <p className="text-sm font-medium text-white mb-2">SP 3-Year</p>
                          <div className="flex items-center gap-2">
                            <input type="number" min="0" max="80" value={discountSettings.sp_3year_discount} onChange={(e) => setDiscountSettings(prev => ({...prev, sp_3year_discount: Number(e.target.value)}))} className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white" />
                            <span className="text-slate-400">%</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">Off EA price</p>
                        </div>
                      </div>
                      <button onClick={saveDiscountSettings} className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors">Save Discount Settings</button>
                    </div>

                    {/* Phase 2: Background Jobs Status */}
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                      <div className="flex items-center gap-3 mb-6"><Clock className="w-5 h-5 text-cyan-400" /><h3 className="font-semibold text-white">Background Jobs</h3></div>
                      {schedulerStatus ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 mb-4">
                            <span className={`w-2 h-2 rounded-full ${schedulerStatus.running ? 'bg-green-400' : 'bg-red-400'}`} />
                            <span className="text-sm text-slate-400">Scheduler {schedulerStatus.running ? 'Running' : 'Stopped'}</span>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            {schedulerStatus.jobs?.map((job: any) => (
                              <div key={job.id} className="flex justify-between items-center bg-slate-800/50 rounded-lg p-3">
                                <span className="text-sm text-white">{job.name}</span>
                                <span className="text-xs text-slate-400">Next: {job.next_run ? new Date(job.next_run).toLocaleTimeString() : 'N/A'}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                          <Clock className="w-8 h-8 mb-2 opacity-50" />
                          <p className="text-sm">Scheduler not available</p>
                          <p className="text-xs mt-1">Phase 2 features require Azure connection</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
      </main>

      {/* Chat Widget */}
      <div className="fixed bottom-6 right-6 z-50">
        {chatOpen && (
          <div className="absolute bottom-16 right-0 w-96 bg-slate-900 rounded-xl border border-slate-700 shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-800/50">
              <div className="flex items-center gap-2"><MessageSquare className="w-5 h-5 text-blue-400" /><span className="font-semibold text-white">FinOps AI Assistant</span></div>
              <button onClick={() => setChatOpen(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="h-80 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((m: any, i: number) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs rounded-lg p-3 text-sm ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'}`}><p className="whitespace-pre-wrap">{m.content}</p></div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-800">
              <div className="flex gap-2">
                <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleChat()} placeholder="Ask about costs..." className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500" />
                <button onClick={handleChat} className="px-3 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"><Send className="w-4 h-4 text-white" /></button>
              </div>
            </div>
          </div>
        )}
        <button onClick={() => setChatOpen(!chatOpen)} className="w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center shadow-lg hover:bg-blue-700"><MessageSquare className="w-6 h-6 text-white" /></button>
      </div>

      {/* Alert Investigation Modal */}
      {alertModalOpen && selectedAlert && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setAlertModalOpen(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-3xl mx-4 shadow-2xl max-h-screen overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${selectedAlert.severity === 'critical' ? 'bg-red-500/20' : 'bg-yellow-500/20'}`}>
                    <AlertTriangle className={`w-5 h-5 ${selectedAlert.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{selectedAlert.resource}</h3>
                    <p className="text-sm text-slate-400">{selectedAlert.message}</p>
                  </div>
                </div>
                <button onClick={() => setAlertModalOpen(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">Cost Impact</p>
                  <p className="text-xl font-bold text-red-400">{selectedAlert.delta}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">Severity</p>
                  <p className={`text-xl font-bold ${selectedAlert.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}`}>{selectedAlert.severity?.toUpperCase() || 'INFO'}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">Detected</p>
                  <p className="text-sm font-medium text-white">{new Date().toLocaleTimeString()}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">Status</p>
                  <p className={`text-sm font-medium ${selectedAlert.status === 'investigating' ? 'text-yellow-400' : selectedAlert.status === 'owner-notified' ? 'text-blue-400' : 'text-white'}`}>{selectedAlert.status || 'new'}</p>
                </div>
              </div>

              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-slate-400">Investigation Workflow</p>
                  {investigationRunning && <span className="text-xs text-blue-400 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Running...</span>}
                  {workflowStep === 4 && <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Complete</span>}
                </div>
                <div className="space-y-3">
                  {[
                    { step: 1, label: 'Analyzing resource metrics in Azure Monitor', agent: 'Cost Sentinel' },
                    { step: 2, label: 'Identifying root cause and anomaly pattern', agent: 'GPT-5' },
                    { step: 3, label: 'Cross-validating findings with historical data', agent: 'Cost Validator' },
                    { step: 4, label: 'Generating remediation recommendations', agent: 'Recommendation Engine' },
                  ].map(({ step, label, agent }) => (
                    <div key={step} className="flex items-center gap-3 text-sm">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${
                        workflowStep > step ? 'bg-green-500/20' : workflowStep === step ? 'bg-blue-500/20' : 'bg-slate-700/60'
                      }`}>
                        {workflowStep > step ? <CheckCircle className="w-3 h-3 text-green-400" /> : 
                         workflowStep === step && investigationRunning ? <Loader2 className="w-3 h-3 text-blue-400 animate-spin" /> :
                         <span className={`text-xs ${workflowStep === step ? 'text-blue-400' : 'text-slate-500'}`}>{step}</span>}
                      </div>
                      <span className={`flex-1 ${workflowStep > step ? 'text-slate-500 line-through' : workflowStep === step ? 'text-white' : 'text-slate-400'}`}>{label}</span>
                      <span className="text-xs text-slate-500">{agent}</span>
                    </div>
                  ))}
                </div>
              </div>

              {workflowStep >= 4 && (
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-3">Recommended Actions</p>
                  <div className="space-y-2">
                    {getRecommendationsForAlert(selectedAlert).map((rec, i) => (
                      <div key={i} className="flex items-center justify-between bg-slate-900/50 rounded-lg p-3">
                        <span className="text-sm text-slate-300">{rec.title}</span>
                        <button className="px-3 py-1 bg-blue-600/20 text-blue-400 text-xs rounded hover:bg-blue-600/30">{rec.action}</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {emailStage !== 'idle' && (
                <div className="bg-slate-800/50 rounded-lg p-4 border border-blue-500/30">
                  <p className="text-xs text-slate-400 mb-3">Email Notification to Resource Owner</p>
                  <div className="bg-slate-900/70 rounded-lg p-4 space-y-2 text-sm">
                    <div className="flex gap-2"><span className="text-slate-500">To:</span><span className="text-white">{getOwnerEmail(selectedAlert)}</span></div>
                    <div className="flex gap-2"><span className="text-slate-500">Subject:</span><span className="text-white">Cost Alert: {selectedAlert.resource}</span></div>
                    <div className="border-t border-slate-700 pt-3 mt-3 text-slate-300 whitespace-pre-wrap text-xs">
{`Hi,

An automated FinOps guardrail detected a ${(selectedAlert.severity || 'info').toUpperCase()} cost event:

Resource: ${selectedAlert.resource}
Impact: ${selectedAlert.delta}
Details: ${selectedAlert.message}

Recommended actions:
${getRecommendationsForAlert(selectedAlert).map(r => `- ${r.title}`).join('\n')}

Please review and take appropriate action.

Thanks,
FinOps AI Command Center`}
                    </div>
                  </div>
                  {emailStage === 'preview' && (
                    <div className="flex gap-2 mt-4 justify-end">
                      <button onClick={() => setEmailStage('idle')} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm">Cancel</button>
                      <button onClick={() => handleAlertAction('send-email')} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm flex items-center gap-2"><Send className="w-4 h-4" /> Send Email (Simulated)</button>
                    </div>
                  )}
                  {emailStage === 'sent' && (
                    <div className="mt-4 flex items-center gap-2 text-green-400 text-sm"><CheckCircle className="w-4 h-4" /> Email sent successfully (simulated)</div>
                  )}
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-800 flex flex-wrap gap-3">
              <button onClick={() => handleAlertAction('investigate')} disabled={investigationRunning} className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2">
                {investigationRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} {investigationRunning ? 'Investigating...' : 'Investigate'}
              </button>
              <button onClick={() => handleAlertAction('notify')} disabled={workflowStep < 4} className="flex-1 py-2 px-4 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2">
                <Send className="w-4 h-4" /> Notify Owner
              </button>
              <button onClick={() => handleAlertAction('remediate')} className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2">
                <Zap className="w-4 h-4" /> Auto-Remediate
              </button>
              <button onClick={() => handleAlertAction('escalate')} className="flex-1 py-2 px-4 bg-orange-600 hover:bg-orange-700 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2">
                <Bell className="w-4 h-4" /> Escalate
              </button>
              <button onClick={() => handleAlertAction('dismiss')} className="py-2 px-4 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 text-sm font-medium">
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deep-Dive Drawer for Recommendation Details */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="flex-1 bg-black/40" onClick={() => setIsDrawerOpen(false)} />
          <div className="w-full max-w-xl h-full bg-slate-950 border-l border-slate-800 p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Recommendation Details</h2>
              <button onClick={() => setIsDrawerOpen(false)} className="text-slate-400 hover:text-white"><X className="w-6 h-6" /></button>
            </div>

            {isDetailsLoading ? (
              <div className="flex items-center justify-center py-12"><div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" /></div>
            ) : (
              <div className="space-y-6">
                {/* Resource Summary */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Resource</h3>
                  <p className="text-lg font-semibold text-white">{selectedRec?.resource || selectedRec?.sku || selectedRec?.resource_id?.split('/').pop() || 'Resource'}</p>
                  <p className="text-sm text-slate-400">{selectedRec?.type || selectedRec?.recommendation_type || 'RI'} - ${(selectedRec?.monthly_cost || selectedRec?.net_savings || 0).toLocaleString()}/mo</p>
                </div>

                {/* Workload Context */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Workload / Application</h3>
                  {selectedRec?.workload?.name || selectedDetails?.workload?.name ? (
                    <div>
                      <p className="text-lg font-semibold text-white">{selectedRec?.workload?.name || selectedDetails?.workload?.name}</p>
                      <p className="text-sm text-slate-400 mb-3">{selectedDetails?.workload?.status?.toUpperCase()} - {selectedDetails?.workload?.criticality || 'standard'} criticality</p>
                    </div>
                  ) : (
                    <p className="text-slate-500 mb-3">No workload assigned</p>
                  )}
                  <label className="text-xs text-slate-400">Application Context (e.g., "PACS - Picture Archiving System for radiology")</label>
                  <textarea 
                    value={workloadContext} 
                    onChange={e => setWorkloadContext(e.target.value)}
                    placeholder="Add context to help AI agents make better decisions..."
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white min-h-[80px]"
                  />
                  <button onClick={saveWorkloadContext} className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white">Save Context</button>
                </div>

                {/* AI Analysis */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-3">AI Agent Analysis</h3>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-xs text-slate-400">Risk Score</p>
                      <p className={`text-2xl font-bold ${(selectedRec?.intelligence?.risk_score || selectedDetails?.agent_analysis?.risk_score || 0) <= 3 ? 'text-green-400' : (selectedRec?.intelligence?.risk_score || selectedDetails?.agent_analysis?.risk_score || 0) <= 6 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {(selectedRec?.intelligence?.risk_score || selectedDetails?.agent_analysis?.risk_score || 0).toFixed(1)}/10
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-400">Confidence</p>
                      <p className="text-2xl font-bold text-purple-400">{selectedRec?.intelligence?.confidence || selectedDetails?.agent_analysis?.confidence || 85}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-400">Action</p>
                      <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                        (selectedRec?._action || selectedRec?.intelligence?.action) === 'approve' ? 'bg-green-500/20 text-green-400' :
                        (selectedRec?._action || selectedRec?.intelligence?.action) === 'modify' ? 'bg-blue-500/20 text-blue-400' :
                        (selectedRec?._action || selectedRec?.intelligence?.action) === 'hold' ? 'bg-yellow-500/20 text-yellow-400' :
                        (selectedRec?._action || selectedRec?.intelligence?.action) === 'block' ? 'bg-red-500/20 text-red-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {(selectedRec?._action || selectedRec?.intelligence?.action || 'APPROVE').toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <p className="text-sm text-slate-300">{selectedRec?.intelligence?.reason || selectedDetails?.agent_analysis?.summary || 'No blocking factors identified. Safe to commit.'}</p>
                  </div>
                </div>

                {/* Blocking Evaluation */}
                {(selectedRec?.evaluation || selectedDetails?.evaluation) && (
                  <div className="bg-amber-900/20 rounded-lg p-4 border border-amber-500/30">
                    <h3 className="text-sm font-medium text-amber-400 mb-2">Blocking SaaS Evaluation</h3>
                    <p className="text-lg font-semibold text-white">{selectedRec?.evaluation?.name || selectedDetails?.evaluation?.name}</p>
                    <p className="text-sm text-slate-400 mb-2">Status: {selectedRec?.evaluation?.status || selectedDetails?.evaluation?.status}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-amber-400">Decision Date: {selectedRec?.evaluation?.decision_date || selectedDetails?.evaluation?.decision_date || 'TBD'}</span>
                      <span className="text-amber-400">Adoption Risk: {selectedRec?.evaluation?.adoption_probability || selectedDetails?.evaluation?.adoption_probability || 50}%</span>
                    </div>
                    <button 
                      onClick={openReEvalPrompt} 
                      disabled={isReevaluating}
                      className="mt-3 px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded text-sm text-white flex items-center gap-2"
                    >
                      {isReevaluating ? <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> : <RefreshCw className="w-4 h-4" />}
                      Re-evaluate with AI Agents
                    </button>
                  </div>
                )}

                {/* Supporting Documents */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Supporting Documents
                  </h3>
                  
                  {/* Uploaded Documents List */}
                  {uploadedDocs.length > 0 ? (
                    <div className="space-y-2 mb-4">
                      {uploadedDocs.map((doc, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-slate-800/50 rounded px-3 py-2">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-blue-400" />
                            <span className="text-sm text-white">{doc.name}</span>
                            <span className="text-xs text-slate-500">({(doc.size / 1024).toFixed(1)} KB)</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => window.open(doc.url, '_blank')} className="text-xs text-blue-400 hover:text-blue-300">View</button>
                            <button onClick={() => setUploadedDocs(uploadedDocs.filter((_, i) => i !== idx))} className="text-xs text-red-400 hover:text-red-300">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 mb-4">No documents uploaded</p>
                  )}
                  
                  {/* File Drop Zone */}
                  <div 
                    className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-lg p-4 text-center cursor-pointer transition-colors"
                    onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('border-blue-500', 'bg-blue-500/10') }}
                    onDragLeave={(e) => { e.preventDefault(); e.currentTarget.classList.remove('border-blue-500', 'bg-blue-500/10') }}
                    onDrop={(e) => {
                      e.preventDefault()
                      e.currentTarget.classList.remove('border-blue-500', 'bg-blue-500/10')
                      const files = Array.from(e.dataTransfer.files)
                      handleDocumentUpload(files)
                    }}
                    onClick={() => document.getElementById('doc-upload-input')?.click()}
                  >
                    <Upload className="w-6 h-6 text-slate-500 mx-auto mb-2" />
                    <p className="text-sm text-slate-400">Drop files here or click to upload</p>
                    <p className="text-xs text-slate-500 mt-1">Supports: PDF, Word, Excel</p>
                  </div>
                  <input 
                    id="doc-upload-input" 
                    type="file" 
                    multiple 
                    accept=".pdf,.doc,.docx,.xls,.xlsx"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files) handleDocumentUpload(Array.from(e.target.files))
                    }}
                  />
                  
                  {/* Re-run AI Analysis Button */}
                  <button 
                    onClick={openReEvalPrompt}
                    disabled={isReevaluating}
                    className="mt-4 w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded text-sm text-white flex items-center justify-center gap-2"
                  >
                    {isReevaluating ? <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> : <RefreshCw className="w-4 h-4" />}
                    Re-run AI Analysis
                  </button>
                </div>

                {/* Manual Override */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-3">Manual Override</h3>
                  <p className="text-xs text-slate-500 mb-3">Override the AI recommendation with your own decision. This takes priority over agent analysis.</p>
                  <div className="grid grid-cols-4 gap-2">
                    <button onClick={() => setOverride('approve', 'Manual approval by user')} className="py-2 px-3 bg-green-600 hover:bg-green-700 rounded text-sm text-white">APPROVE</button>
                    <button onClick={() => setOverride('modify', 'Reduce term length')} className="py-2 px-3 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white">MODIFY</button>
                    <button onClick={() => setOverride('hold', 'Wait for evaluation')} className="py-2 px-3 bg-yellow-600 hover:bg-yellow-700 rounded text-sm text-white">HOLD</button>
                    <button onClick={() => setOverride('block', 'Do not commit')} className="py-2 px-3 bg-red-600 hover:bg-red-700 rounded text-sm text-white">BLOCK</button>
                  </div>
                </div>

                {/* Models Used */}
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">AI Models Consulted</h3>
                  <div className="flex flex-wrap gap-2">
                    {['GPT-5', 'O3', 'O4-Mini', 'GPT-4.1'].map(model => (
                      <span key={model} className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded">{model}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Re-evaluation Prompt Dialog */}
      {showReEvalPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 w-[400px] border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-2">What changed?</h3>
            <p className="text-sm text-slate-400 mb-4">Help the AI focus on what's new (optional)</p>
            
            <div className="space-y-3 mb-6">
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={reEvalTriggers.new_document}
                  onChange={(e) => setReEvalTriggers({...reEvalTriggers, new_document: e.target.checked})}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                />
                <span className="text-sm text-slate-300">New document uploaded</span>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={reEvalTriggers.status_change}
                  onChange={(e) => setReEvalTriggers({...reEvalTriggers, status_change: e.target.checked})}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                />
                <span className="text-sm text-slate-300">Evaluation status updated</span>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={reEvalTriggers.new_context}
                  onChange={(e) => setReEvalTriggers({...reEvalTriggers, new_context: e.target.checked})}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                />
                <span className="text-sm text-slate-300">New context/information added</span>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={reEvalTriggers.decision_date_passed}
                  onChange={(e) => setReEvalTriggers({...reEvalTriggers, decision_date_passed: e.target.checked})}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                />
                <span className="text-sm text-slate-300">Decision date passed</span>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={reEvalTriggers.fresh_analysis}
                  onChange={(e) => setReEvalTriggers({...reEvalTriggers, fresh_analysis: e.target.checked})}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                />
                <span className="text-sm text-slate-300">Just want a fresh analysis</span>
              </label>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => setShowReEvalPrompt(false)}
                className="flex-1 py-2 px-4 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white"
              >
                Cancel
              </button>
              <button 
                onClick={handleReevaluate}
                className="flex-1 py-2 px-4 bg-amber-600 hover:bg-amber-700 rounded text-sm text-white flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Run Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="border-t border-slate-800 bg-slate-900/50 px-6 py-4 mt-6">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Azure FinOps AI Command Center v2.0 - Powered by Azure AI Foundry</span>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-400" />{agents.length} AI Agents Active</span>
            <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-400" />8 Guardrails Enabled</span>
            <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-purple-400" />${((stats?.ai_savings || 0) / 1000).toFixed(0)}K/mo Savings</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
