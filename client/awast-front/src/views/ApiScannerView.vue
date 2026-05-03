<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import ApiScannerForm from '../components/apiScanner/ApiScannerForm.vue'
import ApiScannerProgress from '../components/apiScanner/ApiScannerProgress.vue'
import ApiScannerResults from '../components/apiScanner/ApiScannerResults.vue'
import { apiScannerService } from '../services/apiScannerService'
import type { ApiScanConfig, AnalyzeResponse, ScanJobStatus } from '../types/apiScanner'

type ScanState = 'idle' | 'scanning' | 'completed' | 'failed'

const state = ref<ScanState>('idle')
const jobId = ref('')
const currentJob = ref<ScanJobStatus | null>(null)
const scanResult = ref<AnalyzeResponse | null>(null)
const errorMessage = ref('')

let pollTimer: ReturnType<typeof setTimeout> | null = null

const poll = async () => {
  if (state.value !== 'scanning' || !jobId.value) return
  try {
    const job = await apiScannerService.getJobStatus(jobId.value)
    currentJob.value = job

    if (job.status === 'completed') {
      const result = await apiScannerService.getResult(jobId.value)
      scanResult.value = result
      state.value = 'completed'
      scrollToResults()
    } else if (job.status === 'failed') {
      errorMessage.value = job.error ?? 'Scan failed without an error message.'
      state.value = 'failed'
    } else {
      pollTimer = setTimeout(poll, 2500)
    }
  } catch {
    errorMessage.value = 'Lost connection to API Scanner. Is it running at localhost:1500?'
    state.value = 'failed'
  }
}

const handleScan = async (config: ApiScanConfig) => {
  state.value = 'scanning'
  errorMessage.value = ''
  currentJob.value = null
  scanResult.value = null

  try {
    const { job_id } = await apiScannerService.startScan(config)
    jobId.value = job_id
    poll()
  } catch {
    errorMessage.value = 'Failed to start scan. Is the API Scanner running at localhost:1500?'
    state.value = 'failed'
  }
}

const resetScan = () => {
  if (pollTimer) clearTimeout(pollTimer)
  state.value = 'idle'
  jobId.value = ''
  currentJob.value = null
  scanResult.value = null
  errorMessage.value = ''
}

const downloadReport = () => {
  window.location.href = apiScannerService.getReportUrl(jobId.value)
}

const scrollToResults = () => {
  setTimeout(() => {
    document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})
</script>

<template>
  <div class="scanner-container">
    <!-- Header -->
    <div class="header-section mb-8">
      <v-container>
        <div class="d-flex align-center justify-center flex-column text-center">
          <div class="icon-badge mb-4">
            <v-icon icon="mdi-radar" size="48" color="white"></v-icon>
          </div>
          <h1 class="text-h3 font-weight-bold text-white mb-2">API Security Scanner</h1>
          <p class="text-subtitle-1 text-white opacity-90" style="max-width: 620px">
            Upload your OpenAPI spec and run deep security analysis — static checks, live endpoint verification, BOLA/BFLA, injection, and more.
          </p>
        </div>
      </v-container>
    </div>

    <v-container>

      <!-- Idle: show form -->
      <v-row v-if="state === 'idle'" justify="center">
        <v-col cols="12" md="9" lg="7">
          <ApiScannerForm @scan="handleScan" />
        </v-col>
      </v-row>

      <!-- Scanning: show progress -->
      <v-row v-else-if="state === 'scanning'" justify="center">
        <v-col cols="12" md="8" lg="6">
          <ApiScannerProgress :job="currentJob" />
        </v-col>
      </v-row>

      <!-- Failed: show error -->
      <v-row v-else-if="state === 'failed'" justify="center">
        <v-col cols="12" md="8" lg="6">
          <v-alert type="error" variant="tonal" class="mb-4" rounded="xl">
            <strong>Scan failed</strong><br>
            <span class="text-body-2">{{ errorMessage }}</span>
          </v-alert>
          <v-btn block variant="outlined" color="primary" @click="resetScan" prepend-icon="mdi-arrow-left">
            Try Again
          </v-btn>
        </v-col>
      </v-row>

      <!-- Completed: show results -->
      <div v-else-if="state === 'completed' && scanResult" id="results-section">
        <div class="d-flex justify-space-between align-center mb-6">
          <v-btn
            variant="text"
            prepend-icon="mdi-arrow-left"
            color="primary"
            @click="resetScan"
          >
            New Scan
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-download"
            rounded="lg"
            @click="downloadReport"
          >
            Download HTML Report
          </v-btn>
        </div>

        <ApiScannerResults :result="scanResult" :job-id="jobId" />
      </div>

    </v-container>
  </div>
</template>

<style scoped>
.scanner-container {
  min-height: 100vh;
  background-color: #f8fafc;
  padding-bottom: 60px;
}

.header-section {
  background: linear-gradient(135deg, #0f766e 0%, #0369a1 100%);
  padding: 60px 0 80px;
  position: relative;
}

.header-section::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: #f8fafc;
  border-radius: 40px 40px 0 0;
}

.icon-badge {
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}
</style>
