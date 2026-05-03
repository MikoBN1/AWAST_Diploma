<script setup lang="ts">
import { computed } from 'vue'
import type { ScanJobStatus } from '../../types/apiScanner'

const props = defineProps<{
  job: ScanJobStatus | null
}>()

const phases = [
  { key: 'parsing', label: 'Parsing spec', icon: 'mdi-file-search-outline' },
  { key: 'static_analysis', label: 'Static analysis', icon: 'mdi-code-braces' },
  { key: 'live_verification', label: 'Live verification', icon: 'mdi-web-check' },
  { key: 'building_report', label: 'Building report', icon: 'mdi-chart-bar' },
]

const currentPhaseIndex = computed(() => {
  const phase = props.job?.phase
  if (!phase) return -1
  return phases.findIndex(p => p.key === phase)
})

const phaseLabel = computed(() => {
  const phase = props.job?.phase
  if (!phase) return 'Initializing…'
  return phases.find(p => p.key === phase)?.label ?? phase.replace(/_/g, ' ')
})

const progress = computed(() => props.job?.progress_percent ?? 0)
</script>

<template>
  <v-card class="progress-card" elevation="0">
    <v-card-text class="pa-8 text-center">
      <div class="pulse-ring mb-6">
        <v-progress-circular
          :model-value="progress"
          color="primary"
          size="96"
          width="8"
          class="progress-circle"
        >
          <span class="text-h6 font-weight-bold text-primary">{{ progress }}%</span>
        </v-progress-circular>
      </div>

      <h3 class="text-h5 font-weight-bold text-slate-800 mb-1">Scanning in Progress</h3>
      <p class="text-body-2 text-grey-darken-1 mb-6">
        {{ job?.spec_filename ?? 'Spec file' }}
        <span v-if="job?.base_url"> → {{ job.base_url }}</span>
      </p>

      <!-- Phase stepper -->
      <div class="phases mb-6">
        <div
          v-for="(phase, i) in phases"
          :key="phase.key"
          class="phase-item"
          :class="{
            'phase--done': i < currentPhaseIndex,
            'phase--active': i === currentPhaseIndex,
            'phase--pending': i > currentPhaseIndex,
          }"
        >
          <div class="phase-dot">
            <v-icon
              v-if="i < currentPhaseIndex"
              icon="mdi-check"
              size="14"
              color="white"
            ></v-icon>
            <v-icon
              v-else-if="i === currentPhaseIndex"
              :icon="phase.icon"
              size="14"
              color="white"
            ></v-icon>
          </div>
          <span class="phase-label">{{ phase.label }}</span>
          <div v-if="i < phases.length - 1" class="phase-connector"></div>
        </div>
      </div>

      <div class="status-chip">
        <v-chip
          :prepend-icon="job?.status === 'queued' ? 'mdi-clock-outline' : 'mdi-loading mdi-spin'"
          color="primary"
          variant="tonal"
        >
          {{ phaseLabel }}
        </v-chip>
        <v-chip
          v-if="job && job.findings_count > 0"
          prepend-icon="mdi-bug-outline"
          color="warning"
          variant="tonal"
          class="ml-2"
        >
          {{ job.findings_count }} finding{{ job.findings_count !== 1 ? 's' : '' }} so far
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.progress-card {
  background: white;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.pulse-ring {
  display: inline-block;
  position: relative;
}

.phases {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
}

.phase-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
  max-width: 90px;
}

.phase-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.phase--done .phase-dot {
  background: #10b981;
}

.phase--active .phase-dot {
  background: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.2);
}

.phase--pending .phase-dot {
  background: #e5e7eb;
}

.phase-label {
  font-size: 11px;
  font-weight: 500;
  text-align: center;
  line-height: 1.3;
  color: #6b7280;
}

.phase--active .phase-label {
  color: #4f46e5;
  font-weight: 700;
}

.phase--done .phase-label {
  color: #10b981;
}

.phase-connector {
  position: absolute;
  top: 16px;
  left: calc(50% + 16px);
  right: calc(-50% + 16px);
  height: 2px;
  background: #e5e7eb;
  z-index: 0;
}

.phase--done + .phase-item .phase-connector,
.phase--done .phase-connector {
  background: #10b981;
}

.status-chip {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
