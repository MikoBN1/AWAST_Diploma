<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';
import chainService from '@/services/chainService';
import type { ChainAnalysisResult, AttackChain } from '@/types/api';

const router = useRouter();
const scanStore = useScanStore();
const { alerts } = storeToRefs(scanStore);

const isLoading = ref(false);
const errorMsg = ref('');
const result = ref<ChainAnalysisResult | null>(null);
const expandedChains = ref<Set<string>>(new Set());

const toggleChain = (id: string) => {
  if (expandedChains.value.has(id)) {
    expandedChains.value.delete(id);
  } else {
    expandedChains.value.add(id);
  }
};

const criticalCount = computed(() => result.value?.summary.by_impact.Critical ?? 0);
const highCount = computed(() => result.value?.summary.by_impact.High ?? 0);
const mediumCount = computed(() => result.value?.summary.by_impact.Medium ?? 0);

const impactCfg: Record<string, { color: string; bg: string; icon: string }> = {
  Critical: { color: '#ff0844', bg: 'rgba(255, 8, 68, 0.1)', icon: 'mdi-alert-octagon' },
  High:     { color: '#ff6b35', bg: 'rgba(255, 107, 53, 0.1)', icon: 'mdi-alert' },
  Medium:   { color: '#ffd93d', bg: 'rgba(255, 217, 61, 0.15)', icon: 'mdi-alert-circle' },
  Low:      { color: '#6bcf7f', bg: 'rgba(107, 207, 127, 0.1)', icon: 'mdi-information' },
};

const getImpact = (impact: string) => impactCfg[impact] ?? impactCfg.Low;

const scoreColor = (score: number) => {
  if (score >= 8) return '#ff0844';
  if (score >= 6) return '#ff6b35';
  if (score >= 4) return '#ffd93d';
  return '#6bcf7f';
};

const runAnalysis = async () => {
  if (!alerts.value.length) {
    errorMsg.value = 'No vulnerabilities available. Run a scan first.';
    return;
  }
  isLoading.value = true;
  errorMsg.value = '';
  try {
    result.value = await chainService.analyzeChains(alerts.value);
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || 'Failed to analyze attack chains';
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  if (alerts.value.length > 0) {
    runAnalysis();
  }
});
</script>

<template>
  <div class="chain-page">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="icon-badge mb-4">
          <v-icon icon="mdi-link-variant" size="48" color="white"></v-icon>
        </div>
        <h1 class="text-h3 font-weight-bold text-white mb-3">Attack Chain Analysis</h1>
        <p class="text-subtitle-1 text-white-secondary mb-0">
          Discover how individual vulnerabilities combine into multi-step attack scenarios
        </p>
      </div>
    </div>

    <v-container class="px-4">
      <!-- No alerts state -->
      <v-row v-if="!alerts.length && !isLoading" justify="center" class="mb-8">
        <v-col cols="12" md="6">
          <v-card class="text-center pa-10 rounded-xl" elevation="0" style="border: 2px dashed rgba(99,102,241,0.3)">
            <v-icon icon="mdi-shield-search" size="64" color="grey-lighten-1" class="mb-4"></v-icon>
            <h3 class="text-h6 font-weight-bold text-grey-darken-2 mb-2">No Scan Data Available</h3>
            <p class="text-body-2 text-grey mb-4">Run a vulnerability scan first, then analyze the results for attack chains.</p>
            <v-btn color="primary" variant="elevated" class="text-none font-weight-bold" prepend-icon="mdi-radar" @click="router.push('/scanner')">
              Go to Scanner
            </v-btn>
          </v-card>
        </v-col>
      </v-row>

      <!-- Loading -->
      <v-row v-if="isLoading" justify="center" class="my-12">
        <v-col cols="12" class="text-center">
          <v-progress-circular indeterminate size="64" width="5" color="deep-purple"></v-progress-circular>
          <p class="text-subtitle-1 text-grey-darken-1 mt-4">Analyzing vulnerability chains...</p>
        </v-col>
      </v-row>

      <!-- Error -->
      <v-alert v-if="errorMsg" type="error" variant="tonal" class="mb-6" closable @click:close="errorMsg = ''">{{ errorMsg }}</v-alert>

      <!-- Results -->
      <template v-if="result && !isLoading">
        <!-- Summary chips -->
        <v-row class="mb-8">
          <v-col cols="6" md="3">
            <v-card class="summary-chip rounded-xl pa-5 text-center" elevation="0">
              <div class="chip-value text-deep-purple">{{ result.total_chains_discovered }}</div>
              <div class="chip-label">Chains Found</div>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="summary-chip rounded-xl pa-5 text-center" elevation="0">
              <div class="chip-value" style="color: #ff0844">{{ criticalCount }}</div>
              <div class="chip-label">Critical</div>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="summary-chip rounded-xl pa-5 text-center" elevation="0">
              <div class="chip-value" style="color: #ff6b35">{{ highCount + mediumCount }}</div>
              <div class="chip-label">High / Medium</div>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="summary-chip rounded-xl pa-5 text-center" elevation="0">
              <div class="chip-value" :style="{ color: scoreColor(result.summary.highest_score) }">
                {{ result.summary.highest_score }}<span class="score-max">/10</span>
              </div>
              <div class="chip-label">Highest Score</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- No chains found -->
        <v-card v-if="result.total_chains_discovered === 0" class="text-center pa-10 rounded-xl mb-8" elevation="0" style="border: 1px solid rgba(107,207,127,0.4); background: rgba(107,207,127,0.05)">
          <v-icon icon="mdi-shield-check" size="56" color="green" class="mb-3"></v-icon>
          <h3 class="text-h6 font-weight-bold text-green-darken-2 mb-2">No Attack Chains Detected</h3>
          <p class="text-body-2 text-grey-darken-1">
            The {{ result.total_vulnerabilities }} vulnerabilities found do not form any known multi-step attack chains.
          </p>
        </v-card>

        <!-- Chain cards -->
        <div class="chains-list">
          <div
            v-for="(chain, idx) in result.chains"
            :key="chain.chain_id"
            class="chain-card"
            :class="{ expanded: expandedChains.has(chain.chain_id) }"
          >
            <!-- Impact bar -->
            <div class="impact-bar" :style="{ background: getImpact(chain.max_impact).color }"></div>

            <div class="chain-card-body">
              <!-- Header row -->
              <div class="chain-header">
                <div class="chain-header-left">
                  <div class="impact-badge" :style="{ background: getImpact(chain.max_impact).bg, color: getImpact(chain.max_impact).color }">
                    <v-icon :icon="getImpact(chain.max_impact).icon" size="16" class="mr-1"></v-icon>
                    {{ chain.max_impact.toUpperCase() }}
                  </div>
                  <span class="chain-index">#{{ idx + 1 }}</span>
                </div>
                <div class="score-ring" :style="{ borderColor: scoreColor(chain.composite_score) }">
                  <span class="score-value" :style="{ color: scoreColor(chain.composite_score) }">{{ chain.composite_score }}</span>
                </div>
              </div>

              <!-- Title -->
              <h3 class="chain-title">{{ chain.name }}</h3>

              <!-- Flow visualization -->
              <div class="chain-flow">
                <template v-for="(step, sIdx) in chain.steps" :key="sIdx">
                  <div v-if="sIdx > 0" class="flow-connector">
                    <div class="connector-line"></div>
                    <v-icon size="14" class="connector-arrow" color="grey-lighten-1">mdi-chevron-right</v-icon>
                  </div>
                  <div class="flow-step" :class="step.vuln_type === 'implied' ? 'step-implied' : 'step-real'">
                    <div class="step-circle">
                      <span>{{ sIdx + 1 }}</span>
                    </div>
                    <div class="step-label">{{ step.description.length > 40 ? step.description.slice(0, 40) + '...' : step.description }}</div>
                  </div>
                </template>
              </div>

              <!-- Expand / Collapse -->
              <v-btn
                variant="text"
                class="expand-btn text-none"
                size="small"
                @click="toggleChain(chain.chain_id)"
              >
                <v-icon size="18" class="mr-1">{{ expandedChains.has(chain.chain_id) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
                {{ expandedChains.has(chain.chain_id) ? 'Less Details' : 'View Details' }}
              </v-btn>

              <!-- Expanded content -->
              <v-expand-transition>
                <div v-if="expandedChains.has(chain.chain_id)" class="chain-details">
                  <!-- Description -->
                  <div class="detail-block">
                    <div class="detail-label"><v-icon size="16" class="mr-1">mdi-text-box-outline</v-icon> Description</div>
                    <p class="detail-text">{{ chain.description }}</p>
                  </div>

                  <!-- Preconditions -->
                  <div class="detail-block">
                    <div class="detail-label"><v-icon size="16" class="mr-1">mdi-lightning-bolt</v-icon> Preconditions</div>
                    <p class="detail-text">{{ chain.preconditions }}</p>
                  </div>

                  <!-- Step details table -->
                  <div class="detail-block">
                    <div class="detail-label"><v-icon size="16" class="mr-1">mdi-format-list-numbered</v-icon> Chain Steps</div>
                    <div class="steps-table">
                      <div v-for="(step, sIdx) in chain.steps" :key="sIdx" class="step-row" :class="step.vuln_type === 'implied' ? 'row-implied' : 'row-real'">
                        <div class="step-num">{{ sIdx + 1 }}</div>
                        <div class="step-info">
                          <div class="step-desc">{{ step.description }}</div>
                          <div v-if="step.vuln_type !== 'implied'" class="step-meta">
                            <v-chip size="x-small" variant="tonal" color="deep-purple" class="mr-1">{{ step.vuln_type }}</v-chip>
                            <span v-if="step.url" class="step-url">{{ step.url }}</span>
                            <span v-if="step.parameter" class="step-param ml-2">param: {{ step.parameter }}</span>
                          </div>
                          <div v-else class="step-meta">
                            <v-chip size="x-small" variant="outlined" color="grey">implied</v-chip>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Affected endpoints -->
                  <div v-if="chain.affected_endpoints.length" class="detail-block">
                    <div class="detail-label"><v-icon size="16" class="mr-1">mdi-target</v-icon> Affected Endpoints</div>
                    <div class="endpoints-list">
                      <v-chip
                        v-for="ep in chain.affected_endpoints"
                        :key="ep"
                        size="small"
                        variant="tonal"
                        color="red-darken-1"
                        class="mr-1 mb-1"
                      >
                        {{ ep }}
                      </v-chip>
                    </div>
                  </div>
                </div>
              </v-expand-transition>
            </div>
          </div>
        </div>

        <!-- Vulnerability type distribution -->
        <v-card v-if="Object.keys(result.summary.vuln_type_distribution).length" class="rounded-xl pa-6 mt-8 mb-8" elevation="0" style="border: 1px solid rgba(99,102,241,0.15)">
          <h3 class="text-subtitle-1 font-weight-bold text-grey-darken-3 mb-4">
            <v-icon size="20" class="mr-2" color="deep-purple">mdi-chart-bar</v-icon>
            Vulnerability Type Distribution
          </h3>
          <div class="type-chips">
            <v-chip
              v-for="(count, vtype) in result.summary.vuln_type_distribution"
              :key="vtype"
              variant="tonal"
              color="deep-purple"
              class="mr-2 mb-2"
            >
              {{ vtype }}
              <span class="font-weight-bold ml-1">{{ count }}</span>
            </v-chip>
          </div>
        </v-card>
      </template>
    </v-container>
  </div>
</template>

<style scoped>
.chain-page {
  min-height: 100vh;
  padding-bottom: 48px;
  background: #f8fafc;
}

/* ─── Hero ───────────────────────────────────────── */
.hero-section {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  padding: 80px 24px 100px;
  position: relative;
  overflow: hidden;
}
.hero-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.4;
}
.hero-content {
  text-align: center;
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
}
.hero-content h1 { text-shadow: 0 2px 20px rgba(0,0,0,0.1); }
.text-white-secondary { color: rgba(255,255,255,0.9); }
.icon-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  background: rgba(255,255,255,0.2);
  border-radius: 24px;
  border: 2px solid rgba(255,255,255,0.3);
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* ─── Summary chips ──────────────────────────────── */
.summary-chip {
  background: white !important;
  border: 1px solid rgba(99,102,241,0.12);
  transition: transform .2s, box-shadow .2s;
}
.summary-chip:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}
.chip-value {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
}
.score-max {
  font-size: 16px;
  font-weight: 500;
  opacity: 0.5;
}
.chip-label {
  font-size: 13px;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ─── Chain cards ────────────────────────────────── */
.chains-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.chain-card {
  position: relative;
  background: white;
  border-radius: 20px;
  border: 1px solid rgba(203,213,225,0.6);
  overflow: hidden;
  transition: transform .2s, box-shadow .2s, border-color .2s;
}
.chain-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 40px rgba(99,102,241,0.1);
  border-color: rgba(99,102,241,0.3);
}
.chain-card.expanded {
  box-shadow: 0 12px 24px rgba(99,102,241,0.12);
  border-color: rgba(99,102,241,0.3);
}
.impact-bar {
  height: 4px;
  width: 100%;
}
.chain-card-body {
  padding: 24px;
}

/* Header */
.chain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.chain-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.impact-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.chain-index {
  font-size: 13px;
  font-weight: 600;
  color: #a0aec0;
}

/* Score ring */
.score-ring {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.score-value {
  font-size: 18px;
  font-weight: 800;
}

/* Title */
.chain-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 16px 0;
  line-height: 1.3;
}

/* ─── Flow visualization ─────────────────────────── */
.chain-flow {
  display: flex;
  align-items: flex-start;
  padding: 16px 0;
  overflow-x: auto;
  gap: 0;
}
.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 90px;
  max-width: 130px;
  text-align: center;
}
.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.step-real .step-circle {
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: white;
  box-shadow: 0 4px 12px rgba(99,102,241,0.35);
}
.step-implied .step-circle {
  background: rgba(113,128,150,0.1);
  color: #a0aec0;
  border: 2px dashed #cbd5e0;
}
.step-label {
  font-size: 11px;
  color: #4a5568;
  line-height: 1.3;
  word-break: break-word;
}
.flow-connector {
  display: flex;
  align-items: center;
  padding-top: 10px;
  margin: 0 2px;
}
.connector-line {
  width: 28px;
  height: 2px;
  background: linear-gradient(90deg, #c4b5fd, #a78bfa);
  border-radius: 1px;
}
.connector-arrow {
  margin-left: -2px;
}

/* ─── Expanded details ───────────────────────────── */
.expand-btn {
  color: #6366f1 !important;
  font-weight: 600;
  margin-top: 8px;
}
.chain-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(203,213,225,0.4);
}
.detail-block {
  margin-bottom: 16px;
}
.detail-label {
  font-size: 13px;
  font-weight: 700;
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}
.detail-text {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.6;
  margin: 0;
}

/* Steps table */
.steps-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.step-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
}
.row-real {
  background: rgba(99,102,241,0.04);
  border-left: 3px solid #6366f1;
}
.row-implied {
  background: rgba(113,128,150,0.04);
  border-left: 3px dashed #cbd5e0;
}
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(99,102,241,0.1);
  color: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}
.row-implied .step-num {
  background: rgba(113,128,150,0.1);
  color: #a0aec0;
}
.step-info {
  flex: 1;
  min-width: 0;
}
.step-desc {
  font-size: 14px;
  color: #2d3748;
  margin-bottom: 4px;
}
.step-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.step-url {
  font-size: 12px;
  color: #718096;
  word-break: break-all;
}
.step-param {
  font-size: 12px;
  color: #a0aec0;
  font-family: 'Courier New', monospace;
}
.endpoints-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* ─── Responsive ─────────────────────────────────── */
@media (max-width: 768px) {
  .chain-flow { flex-wrap: wrap; gap: 8px; }
  .flow-connector { display: none; }
  .flow-step { min-width: 70px; }
  .chain-card-body { padding: 16px; }
}
</style>
