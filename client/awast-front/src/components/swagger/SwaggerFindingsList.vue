<script setup lang="ts">
import { ref } from 'vue'

interface Finding {
  title: string
  description: string
  severity: 'Critical' | 'High' | 'Medium' | 'Low'
  location: string
  remediation: string
}

defineProps<{
  findings: Finding[]
}>()

const expandedItems = ref<Set<number>>(new Set())

const toggleExpand = (index: number) => {
  if (expandedItems.value.has(index)) {
    expandedItems.value.delete(index)
  } else {
    expandedItems.value.add(index)
  }
}

const getSeverityConfig = (severity: string) => {
  const configs: Record<string, any> = {
    Critical: {
      icon: 'mdi-alert-octagon',
      class: 'severity-critical'
    },
    High: {
      icon: 'mdi-alert',
      class: 'severity-high'
    },
    Medium: {
      icon: 'mdi-alert-circle',
      class: 'severity-medium'
    },
    Low: {
      icon: 'mdi-information',
      class: 'severity-low'
    }
  }
  return configs[severity] || configs.Low
}
</script>

<template>
  <div class="findings-list">
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h2 class="text-h5 font-weight-bold text-slate-800">Analysis Findings</h2>
        <p class="text-body-2 text-grey-darken-1">{{ findings.length }} vulnerabilities detected</p>
      </div>
      <!-- You could add filters here later -->
    </div>

    <div
      v-for="(finding, index) in findings"
      :key="index"
      class="finding-card mb-4"
      :class="{ 'expanded': expandedItems.has(index) }"
    >
      <div class="card-content pa-5">
        <div class="d-flex align-start">
          <!-- Severity Icon -->
          <div class="severity-indicator mr-4" :class="getSeverityConfig(finding.severity).class">
            <v-icon :icon="getSeverityConfig(finding.severity).icon" size="24" color="white"></v-icon>
          </div>

          <div class="flex-grow-1">
            <div class="d-flex justify-space-between align-start mb-2">
              <h3 class="text-h6 font-weight-bold text-slate-800">{{ finding.title }}</h3>
              <v-chip
                :color="getSeverityConfig(finding.severity).class.replace('severity-', '') === 'critical' || getSeverityConfig(finding.severity).class.replace('severity-', '') === 'high' ? 'error' : 'warning'"
                variant="tonal"
                size="small"
                class="font-weight-bold ml-2"
              >
                {{ finding.severity.toUpperCase() }}
              </v-chip>
            </div>

            <div class="d-flex align-center mb-3">
              <v-icon icon="mdi-map-marker-path" size="16" color="grey-darken-1" class="mr-1"></v-icon>
              <code class="location-badge">{{ finding.location }}</code>
            </div>

            <p class="text-body-2 text-grey-darken-2 mb-0 description-text">
              {{ finding.description }}
            </p>

            <!-- Expandable Remediation -->
            <div 
              class="remediation-section mt-4"
              v-show="expandedItems.has(index)"
            >
              <div class="d-flex align-center mb-2">
                <v-icon icon="mdi-shield-check" color="success" class="mr-2"></v-icon>
                <span class="font-weight-bold text-success">Recommended Remediation</span>
              </div>
              <p class="text-body-2 text-slate-700 bg-green-lighten-5 pa-3 rounded-lg border-success-light">
                {{ finding.remediation }}
              </p>
            </div>
          </div>
        </div>

        <div class="d-flex justify-end mt-2">
          <v-btn
            variant="text"
            size="small"
            color="primary"
            class="text-none"
            @click="toggleExpand(index)"
          >
            {{ expandedItems.has(index) ? 'Show Less' : 'View Remediation' }}
            <v-icon :icon="expandedItems.has(index) ? 'mdi-chevron-up' : 'mdi-chevron-down'" end></v-icon>
          </v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.finding-card {
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.finding-card:hover {
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
  border-color: rgba(102, 126, 234, 0.2);
}

.severity-indicator {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.severity-critical {
  background: linear-gradient(135deg, #ff0844 0%, #ff6b9d 100%);
  box-shadow: 0 4px 12px rgba(255, 8, 68, 0.3);
}

.severity-high {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
}

.severity-medium {
  background: linear-gradient(135deg, #ffd93d 0%, #f6c244 100%);
  box-shadow: 0 4px 12px rgba(255, 217, 61, 0.3);
}

.severity-low {
  background: linear-gradient(135deg, #6bcf7f 0%, #4facfe 100%);
  box-shadow: 0 4px 12px rgba(107, 207, 127, 0.3);
}

.location-badge {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #475569;
}

.border-success-light {
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.description-text {
  line-height: 1.6;
}

/* Transitions */
.remediation-section {
  transition: all 0.3s ease;
}
</style>
