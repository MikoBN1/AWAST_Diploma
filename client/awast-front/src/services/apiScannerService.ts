import axios from 'axios'
import type { ApiScanConfig, AnalyzeResponse, ScanJobStatus } from '../types/apiScanner'

const SCANNER_BASE_URL = (import.meta.env.VITE_SCANNER_URL as string | undefined) ?? 'http://localhost:1500'

const scannerClient = axios.create({ baseURL: SCANNER_BASE_URL })

export const apiScannerService = {
  async startScan(config: ApiScanConfig): Promise<{ job_id: string; status: string; status_url: string; result_url: string }> {
    const form = new FormData()
    form.append('spec_file', config.spec_file)
    form.append('token_value', config.token_value)

    if (config.base_url) form.append('base_url', config.base_url)
    if (config.secondary_token_value) {
      form.append('secondary_token_value', config.secondary_token_value)
      if (config.secondary_token_type) form.append('secondary_token_type', config.secondary_token_type)
      if (config.secondary_token_location) form.append('secondary_token_location', config.secondary_token_location)
      if (config.secondary_token_name) form.append('secondary_token_name', config.secondary_token_name)
    }
    if (config.cookie_name) form.append('cookie_name', config.cookie_name)
    if (config.cookie_value) form.append('cookie_value', config.cookie_value)
    if (config.api_key_name) form.append('api_key_name', config.api_key_name)
    if (config.api_key_value) form.append('api_key_value', config.api_key_value)
    if (config.api_key_location) form.append('api_key_location', config.api_key_location)
    if (config.max_concurrency != null) form.append('max_concurrency', String(config.max_concurrency))
    if (config.request_delay_ms != null) form.append('request_delay_ms', String(config.request_delay_ms))
    if (config.time_analysis) form.append('time_analysis', 'true')
    if (config.enumerate_mode) form.append('enumerate_mode', 'true')
    if (config.ratelimit_mode) {
      form.append('ratelimit_mode', 'true')
      if (config.ratelimit_burst_count != null) form.append('ratelimit_burst_count', String(config.ratelimit_burst_count))
    }
    if (config.cors_mode) form.append('cors_mode', 'true')
    if (config.header_check_mode) form.append('header_check_mode', 'true')
    if (config.custom_wordlist) form.append('custom_wordlist', config.custom_wordlist)

    const { data } = await scannerClient.post('/analyze', form)
    return data
  },

  async getJobStatus(jobId: string): Promise<ScanJobStatus> {
    const { data } = await scannerClient.get(`/jobs/${jobId}`)
    return data
  },

  async getResult(jobId: string): Promise<AnalyzeResponse> {
    const { data } = await scannerClient.get(`/jobs/${jobId}/result`)
    return data
  },

  getReportUrl(jobId: string): string {
    return `${SCANNER_BASE_URL}/jobs/${jobId}/report`
  },

  async listJobs(): Promise<ScanJobStatus[]> {
    const { data } = await scannerClient.get('/jobs')
    return data
  },

  async deleteJob(jobId: string): Promise<void> {
    await scannerClient.delete(`/jobs/${jobId}`)
  },
}
