<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AnalyzeResponse, Finding } from '../../types/apiScanner'

const props = defineProps<{
  result: AnalyzeResponse
  jobId: string
}>()

const severityFilter = ref<string | null>(null)
const expandedIds = ref<Set<number>>(new Set())

const SEVERITY_CONFIG: Record<string, { color: string; icon: string; bg: string }> = {
  critical: { color: 'error', icon: 'mdi-alert-octagon', bg: 'severity-critical' },
  high: { color: 'deep-orange', icon: 'mdi-alert', bg: 'severity-high' },
  medium: { color: 'warning', icon: 'mdi-alert-circle', bg: 'severity-medium' },
  low: { color: 'success', icon: 'mdi-information', bg: 'severity-low' },
  info: { color: 'info', icon: 'mdi-information-outline', bg: 'severity-info' },
}

const RISK_COLOR: Record<string, string> = {
  CRITICAL: 'error',
  HIGH: 'deep-orange',
  MEDIUM: 'warning',
  LOW: 'success',
  NONE: 'success',
}

const METHOD_COLOR: Record<string, string> = {
  GET: 'success',
  POST: 'primary',
  PUT: 'warning',
  PATCH: 'orange',
  DELETE: 'error',
  HEAD: 'grey',
  OPTIONS: 'grey',
}

const summaryOrder = ['critical', 'high', 'medium', 'low', 'info']

const summaryItems = computed(() =>
  summaryOrder.map(k => ({ key: k, count: props.result.summary[k] ?? 0 }))
)

const filteredFindings = computed<Finding[]>(() => {
  if (!severityFilter.value) return props.result.findings
  return props.result.findings.filter(f => f.severity === severityFilter.value)
})

const FALLBACK_SEVERITY = { color: 'info', icon: 'mdi-information-outline', bg: 'severity-info' }
const severityCfg = (s: string) => SEVERITY_CONFIG[s] ?? FALLBACK_SEVERITY
const methodColor = (m: string) => METHOD_COLOR[m?.toUpperCase()] ?? 'grey'

const toggleFinding = (index: number) => {
  if (expandedIds.value.has(index)) expandedIds.value.delete(index)
  else expandedIds.value.add(index)
}

const totalFindings = computed(() => props.result.findings.length)
</script>

<template>
  <div class="results-root">

    <!-- Summary row -->
    <v-row dense class="mb-4">
      <v-col
        v-for="item in summaryItems"
        :key="item.key"
        cols="auto"
        class="flex-grow-1"
      >
        <v-card
          class="summary-chip text-center pa-4"
          elevation="0"
          :class="{ 'summary-chip--active': severityFilter === item.key }"
          @click="severityFilter = severityFilter === item.key ? null : item.key"
        >
          <div class="text-h4 font-weight-black" :class="`text-${severityCfg(item.key).color}`">{{ item.count }}</div>
          <div class="text-caption font-weight-bold text-uppercase text-grey-darken-1">{{ item.key }}</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Risk Overview + Metadata -->
    <v-row dense class="mb-4">
      <v-col cols="12" md="7">
        <v-card v-if="result.risk_overview" class="result-card pa-5 h-100" elevation="0">
          <div class="d-flex align-center mb-4">
            <v-icon icon="mdi-shield-alert" color="primary" class="mr-2"></v-icon>
            <span class="text-subtitle-1 font-weight-bold">Risk Overview</span>
            <v-spacer></v-spacer>
            <v-chip
              :color="RISK_COLOR[result.risk_overview.overall_risk] ?? 'grey'"
              variant="flat"
              size="small"
              class="font-weight-bold"
            >
              {{ result.risk_overview.overall_risk }}
            </v-chip>
          </div>

          <v-row dense>
            <v-col cols="6">
              <div class="stat-block">
                <div class="text-h5 font-weight-black text-slate-800">{{ result.risk_overview.total_findings }}</div>
                <div class="text-caption text-grey-darken-1">Total Findings</div>
              </div>
            </v-col>
            <v-col cols="6">
              <div class="stat-block">
                <div class="text-h5 font-weight-black text-slate-800">{{ result.risk_overview.auth_coverage_percent }}%</div>
                <div class="text-caption text-grey-darken-1">Auth Coverage</div>
              </div>
            </v-col>
          </v-row>

          <div v-if="result.risk_overview.critical_paths.length" class="mt-3">
            <p class="text-caption font-weight-bold text-uppercase text-grey mb-2">Critical Paths</p>
            <div class="d-flex flex-wrap gap-1">
              <code v-for="path in result.risk_overview.critical_paths" :key="path" class="path-badge">{{ path }}</code>
            </div>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="result-card pa-5 h-100" elevation="0">
          <div class="d-flex align-center mb-4">
            <v-icon icon="mdi-information-outline" color="primary" class="mr-2"></v-icon>
            <span class="text-subtitle-1 font-weight-bold">Scan Metadata</span>
          </div>
          <v-list density="compact" class="pa-0">
            <v-list-item class="px-0 py-1">
              <template #prepend><v-icon icon="mdi-api" size="16" color="grey" class="mr-2"></v-icon></template>
              <v-list-item-title class="text-body-2">{{ result.metadata.endpoint_count }} endpoints</v-list-item-title>
            </v-list-item>
            <v-list-item class="px-0 py-1">
              <template #prepend><v-icon icon="mdi-tag-outline" size="16" color="grey" class="mr-2"></v-icon></template>
              <v-list-item-title class="text-body-2">Spec {{ result.metadata.spec_version }}</v-list-item-title>
            </v-list-item>
            <v-list-item class="px-0 py-1">
              <template #prepend><v-icon icon="mdi-web" size="16" color="grey" class="mr-2"></v-icon></template>
              <v-list-item-title class="text-body-2">Live checks: {{ result.metadata.live_checks_run ? 'Yes' : 'No' }}</v-list-item-title>
            </v-list-item>
            <v-list-item class="px-0 py-1">
              <template #prepend><v-icon icon="mdi-clock-outline" size="16" color="grey" class="mr-2"></v-icon></template>
              <v-list-item-title class="text-body-2">{{ new Date(result.metadata.analyzed_at).toLocaleString() }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <!-- Parser warnings -->
    <v-alert
      v-if="result.parser_warnings.length"
      type="warning"
      variant="tonal"
      class="mb-4"
      density="compact"
      closable
    >
      <strong>{{ result.parser_warnings.length }} parser warning{{ result.parser_warnings.length > 1 ? 's' : '' }}</strong>
      <ul class="mt-1 mb-0">
        <li v-for="w in result.parser_warnings" :key="w" class="text-body-2">{{ w }}</li>
      </ul>
    </v-alert>

    <!-- Findings -->
    <div class="d-flex justify-space-between align-center mb-4">
      <div>
        <h3 class="text-h6 font-weight-bold text-slate-800">Findings</h3>
        <p class="text-body-2 text-grey-darken-1">
          {{ filteredFindings.length }}{{ severityFilter ? ` ${severityFilter}` : '' }}
          of {{ totalFindings }} total
        </p>
      </div>
      <v-btn
        v-if="severityFilter"
        variant="text"
        size="small"
        color="primary"
        prepend-icon="mdi-close"
        @click="severityFilter = null"
      >
        Clear filter
      </v-btn>
    </div>

    <div
      v-for="(finding, index) in filteredFindings"
      :key="index"
      class="finding-card mb-3"
    >
      <div class="pa-5" @click="toggleFinding(index)" style="cursor: pointer">
        <div class="d-flex align-start">
          <div class="severity-badge mr-4" :class="severityCfg(finding.severity).bg">
            <v-icon :icon="severityCfg(finding.severity).icon" size="20" color="white"></v-icon>
          </div>

          <div class="flex-grow-1 min-width-0">
            <div class="d-flex flex-wrap align-center gap-2 mb-1">
              <v-chip
                :color="methodColor(finding.method)"
                variant="flat"
                size="x-small"
                class="font-weight-bold method-chip"
              >{{ finding.method }}</v-chip>
              <code class="endpoint-badge">{{ finding.endpoint }}</code>
              <v-spacer></v-spacer>
              <v-chip
                :color="severityCfg(finding.severity).color"
                variant="tonal"
                size="x-small"
                class="font-weight-bold"
              >{{ finding.severity.toUpperCase() }}</v-chip>
            </div>

            <h4 class="text-body-1 font-weight-bold text-slate-800 mb-1">{{ finding.title }}</h4>

            <div class="d-flex flex-wrap gap-2 mt-2">
              <v-chip size="x-small" variant="outlined" color="grey">{{ finding.category }}</v-chip>
              <v-chip size="x-small" :color="finding.source === 'live' ? 'primary' : 'grey'" variant="tonal">{{ finding.source }}</v-chip>
              <v-chip size="x-small" variant="outlined" :color="finding.confidence === 'high' ? 'success' : finding.confidence === 'medium' ? 'warning' : 'grey'">
                {{ finding.confidence }} confidence
              </v-chip>
              <v-chip size="x-small" variant="outlined" :color="finding.status === 'confirmed' ? 'error' : finding.status === 'probable' ? 'warning' : 'grey'">
                {{ finding.status }}
              </v-chip>
              <v-chip v-if="finding.cwe_id" size="x-small" variant="tonal" color="primary">{{ finding.cwe_id }}</v-chip>
            </div>
          </div>

          <v-icon
            :icon="expandedIds.has(index) ? 'mdi-chevron-up' : 'mdi-chevron-down'"
            color="grey"
            class="ml-2 flex-shrink-0"
          ></v-icon>
        </div>
      </div>

      <!-- Expanded detail -->
      <div v-show="expandedIds.has(index)" class="finding-detail px-5 pb-5">
        <v-divider class="mb-4"></v-divider>

        <v-row dense>
          <v-col cols="12" md="6">
            <p class="detail-label">Evidence</p>
            <p class="text-body-2 text-slate-700">{{ finding.evidence }}</p>
          </v-col>
          <v-col cols="12" md="6">
            <p class="detail-label">Recommendation</p>
            <p class="text-body-2 text-slate-700">{{ finding.recommendation }}</p>
          </v-col>
        </v-row>

        <v-row v-if="finding.owasp_category || finding.attack_type || finding.payload_family" dense class="mt-2">
          <v-col cols="12">
            <div class="d-flex flex-wrap gap-2">
              <v-chip v-if="finding.owasp_category" size="small" variant="tonal" color="deep-orange" prepend-icon="mdi-shield-bug">{{ finding.owasp_category }}</v-chip>
              <v-chip v-if="finding.attack_type" size="small" variant="outlined" color="grey">{{ finding.attack_type }}</v-chip>
              <v-chip v-if="finding.payload_family" size="small" variant="outlined" color="grey">{{ finding.payload_family }}</v-chip>
            </div>
          </v-col>
        </v-row>

        <!-- Risk score -->
        <div v-if="finding.risk_score" class="mt-3">
          <p class="detail-label">Risk Score</p>
          <div class="d-flex align-center gap-3 flex-wrap">
            <v-chip
              v-if="finding.risk_score.cvss_base != null"
              :color="finding.risk_score.cvss_base >= 9 ? 'error' : finding.risk_score.cvss_base >= 7 ? 'deep-orange' : finding.risk_score.cvss_base >= 4 ? 'warning' : 'success'"
              variant="flat"
              size="small"
              class="font-weight-bold"
            >CVSS {{ finding.risk_score.cvss_base.toFixed(1) }}</v-chip>
            <code v-if="finding.risk_score.cvss_vector" class="endpoint-badge text-xs">{{ finding.risk_score.cvss_vector }}</code>
          </div>
        </div>

        <!-- Request evidence -->
        <div v-if="finding.request_evidence" class="mt-3">
          <p class="detail-label">Request Evidence</p>
          <v-card variant="tonal" color="grey" rounded="lg" class="pa-3">
            <div class="d-flex align-center gap-2 mb-2">
              <v-chip :color="methodColor(finding.request_evidence.method)" variant="flat" size="x-small" class="font-weight-bold">
                {{ finding.request_evidence.method }}
              </v-chip>
              <code class="text-body-2 text-slate-700">{{ finding.request_evidence.url }}</code>
              <v-chip
                v-if="finding.request_evidence.status_code"
                :color="finding.request_evidence.status_code < 400 ? 'success' : 'error'"
                variant="tonal"
                size="x-small"
              >{{ finding.request_evidence.status_code }}</v-chip>
            </div>
            <pre v-if="finding.request_evidence.response_snippet" class="response-snippet">{{ finding.request_evidence.response_snippet }}</pre>
          </v-card>
        </div>

        <!-- Narrative -->
        <div v-if="finding.narrative" class="mt-3">
          <p class="detail-label">Analysis Narrative</p>
          <p class="text-body-2 text-slate-700 mb-2">{{ finding.narrative.summary }}</p>
          <ol v-if="finding.narrative.steps?.length" class="narrative-steps">
            <li v-for="step in finding.narrative.steps" :key="step" class="text-body-2 text-slate-600">{{ step }}</li>
          </ol>
        </div>
      </div>
    </div>

    <v-alert v-if="filteredFindings.length === 0" type="success" variant="tonal" class="mt-4">
      No findings match the current filter.
    </v-alert>
  </div>
</template>

<style scoped>
.result-card {
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.summary-chip {
  background: white;
  border-radius: 16px;
  border: 2px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
}

.summary-chip:hover {
  border-color: rgba(79, 70, 229, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07);
}

.summary-chip--active {
  border-color: rgba(79, 70, 229, 0.5);
  background: rgba(79, 70, 229, 0.05) !important;
}

.stat-block {
  padding: 8px 0;
}

.path-badge {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.78rem;
  color: #475569;
  display: inline-block;
  margin: 2px;
}

.finding-card {
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s ease;
}

.finding-card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.severity-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.severity-critical { background: linear-gradient(135deg, #ff0844 0%, #ff6b9d 100%); box-shadow: 0 4px 10px rgba(255, 8, 68, 0.3); }
.severity-high     { background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); box-shadow: 0 4px 10px rgba(255, 107, 53, 0.3); }
.severity-medium   { background: linear-gradient(135deg, #ffd93d 0%, #f6c244 100%); box-shadow: 0 4px 10px rgba(255, 217, 61, 0.3); }
.severity-low      { background: linear-gradient(135deg, #6bcf7f 0%, #4facfe 100%); box-shadow: 0 4px 10px rgba(107, 207, 127, 0.3); }
.severity-info     { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); box-shadow: 0 4px 10px rgba(116, 185, 255, 0.3); }

.endpoint-badge {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.82rem;
  color: #475569;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
  display: inline-block;
}

.method-chip {
  font-size: 11px !important;
  min-width: 48px;
  justify-content: center;
}

.detail-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #9ca3af;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.response-snippet {
  font-size: 12px;
  color: #475569;
  background: transparent;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 120px;
  overflow-y: auto;
}

.narrative-steps {
  padding-left: 20px;
}

.narrative-steps li {
  margin-bottom: 4px;
}

.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.min-width-0 { min-width: 0; }
.text-xs { font-size: 11px; }
</style>
