export interface RiskOverview {
  overall_risk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE'
  total_findings: number
  critical_paths: string[]
  auth_coverage_percent: number
}

export interface RequestEvidence {
  url: string
  method: string
  status_code: number | null
  request_headers: Record<string, string>
  response_snippet: string | null
}

export interface TimingContext {
  baseline_ms: number | null
  observed_ms: number | null
  delta_ms: number | null
}

export interface VerificationNarrative {
  summary: string
  steps: string[]
}

export interface RiskScore {
  cvss_vector: string | null
  cvss_base: number | null
  risk_priority: number
  severity_adjustment_reason: string | null
}

export interface Finding {
  finding_id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  endpoint: string
  method: string
  evidence: string
  recommendation: string
  category: string
  source: 'static' | 'live'
  attack_type: string | null
  payload_family: string | null
  confidence: 'high' | 'medium' | 'low'
  status: 'confirmed' | 'probable' | 'informational'
  cwe_id: string | null
  owasp_category: string | null
  request_evidence: RequestEvidence | null
  timing_context: TimingContext | null
  risk_score: RiskScore | null
  narrative: VerificationNarrative | null
}

export interface FindingGroup {
  group_key: string
  group_type: 'endpoint' | 'attack_family' | 'auth_model'
  findings: Finding[]
  risk_rating: string
}

export interface VerificationRecord {
  endpoint: string
  method: string
  auth_mode: string
  status_code: number | null
  error: string | null
}

export interface AnalyzeMetadata {
  analyzed_at: string
  spec_version: string
  endpoint_count: number
  live_checks_run: boolean
}

export interface AnalyzeResponse {
  summary: Record<string, number>
  risk_overview: RiskOverview | null
  findings: Finding[]
  grouped_findings: FindingGroup[]
  parser_warnings: string[]
  verification: VerificationRecord[]
  metadata: AnalyzeMetadata
}

export interface ScanJobStatus {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress_percent: number
  phase: string | null
  findings_count: number
  spec_filename: string
  base_url: string | null
  created_at: string
  finished_at: string | null
  error: string | null
}

export interface ApiScanConfig {
  spec_file: File
  token_value: string
  base_url?: string
  secondary_token_value?: string
  secondary_token_type?: string
  secondary_token_location?: 'header' | 'cookie' | 'query'
  secondary_token_name?: string
  cookie_name?: string
  cookie_value?: string
  api_key_name?: string
  api_key_value?: string
  api_key_location?: 'header' | 'query'
  max_concurrency?: number
  request_delay_ms?: number
  time_analysis?: boolean
  enumerate_mode?: boolean
  ratelimit_mode?: boolean
  ratelimit_burst_count?: number
  cors_mode?: boolean
  header_check_mode?: boolean
  custom_wordlist?: string
}
