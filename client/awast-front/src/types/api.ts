export interface UserOut {
  user_id: string;
  username: string;
  email: string;
  enabled_domains: string[];
  role: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  role: string;
  enabled_domains: string[];
}

export interface UserUpdate {
  username?: string | null;
  email?: string | null;
  role?: string | null;
  password?: string | null;
  enabled_domains?: string[] | null;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface RequestBody {
  target: string;
  cookies?: Record<string, string>;
}

export interface ChainStep {
  vuln_id: string;
  vuln_type: string;
  vuln_name: string;
  severity: string;
  url: string;
  parameter: string;
  description: string;
}

export interface AttackChain {
  chain_id: string;
  name: string;
  description: string;
  steps: ChainStep[];
  composite_score: number;
  max_impact: string;
  affected_endpoints: string[];
  preconditions: string;
}

export interface ChainAnalysisSummary {
  by_impact: Record<string, number>;
  vuln_type_distribution: Record<string, number>;
  most_chained_endpoints: Array<{ url: string; chain_count: number }>;
  highest_score: number;
}

export interface ChainAnalysisResult {
  total_vulnerabilities: number;
  total_chains_discovered: number;
  chains: AttackChain[];
  summary: ChainAnalysisSummary;
}

export interface ExploiterRequestBody {
  target: string;
  params: string;
  vuln_type: string;
  cookies?: Record<string, string>;
  method: string;
  ws_id?: string;
  previous_payloads?: string[];
}

export interface ExploiterConfirmedResponse {
  status: 'confirmed';
  vuln_type: string;
  target: string;
  parameter: string;
  working_payload: string;
  tried_payloads: string[];
  proof: string;
  curl: string;
  message: string;
}

export interface ExploiterPotentialResponse {
  status: 'potential';
  message: string;
  tried_payloads: string[];
}

export type ExploiterResponse = ExploiterConfirmedResponse | ExploiterPotentialResponse;

export interface ReportRequest {
  scan_id: string;
}

export interface DownloadReportRequest {
  report_id: string;
}

// Additional types inferred from usage or common patterns
export interface GenericResponse {
  [key: string]: any;
}

export interface ScanStatus {
  status: string;
  progress: string;
}

export interface Alert {
  alert: string;
  risk: string;
  url: string;
  param: string;
  description: string;
  solution: string;
}
