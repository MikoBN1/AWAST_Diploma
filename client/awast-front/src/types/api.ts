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
}

export interface ExploiterRequestBody {
  target: string;
  params?: string;
  vuln_type?: string;
  username?: string;
  password?: string;
  login_url?: string;
  method?: string;
}

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
