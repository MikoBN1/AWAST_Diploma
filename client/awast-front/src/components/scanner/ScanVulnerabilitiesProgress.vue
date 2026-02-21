<script setup lang="ts">
import { ref, computed } from "vue";
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';

const scanStore = useScanStore();
const { alerts, totalAlertsFound } = storeToRefs(scanStore);

const vulns = computed(() => {
  let high = 0;
  let medium = 0;
  let low = 0;

  alerts.value.forEach((alert: any) => {
    if (alert.risk === 'High') high++;
    else if (alert.risk === 'Medium') medium++;
    else if (alert.risk === 'Low') low++;
  });

  return [
    {
      severity: "High",
      value: high,
      color: "#ef4444",
      gradient: "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)",
    },
    {
      severity: "Medium",
      value: medium,
      color: "#f59e0b",
      gradient: "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)",
    },
    {
      severity: "Low",
      value: low,
      color: "#10b981",
      gradient: "linear-gradient(90deg, #10b981 0%, #059669 100%)",
    },
  ];
});

const scanType = ref("Full");
</script>

<template>
  <v-card class="progress-card glass-card" elevation="0">
    <v-card-text class="pa-6">
      <div class="card-header mb-6">
        <div class="d-flex align-center mb-2">
          <v-icon icon="mdi-shield-alert" color="primary" size="28" class="mr-3"></v-icon>
          <h3 class="text-h5 font-weight-bold text-slate-800">Vulnerabilities Summary</h3>
        </div>
        <p class="text-body-2 text-grey-darken-1 ml-11">
          Distribution of security issues found by severity level
        </p>
      </div>

      <!-- Progress Bars -->
      <div class="vulnerabilities-list mb-5">
        <div v-for="item in vulns" :key="item.severity" class="vuln-item mb-5">
          <div class="d-flex justify-space-between align-center mb-2">
            <div class="d-flex align-center">
              <div class="severity-badge" :class="`severity-${item.severity.toLowerCase()}`"></div>
              <span class="severity-label">{{ item.severity }}</span>
            </div>
            <span class="severity-value">{{ item.value }} found</span>
          </div>
          <v-progress-linear
            :model-value="alerts.length > 0 ? (item.value / alerts.length) * 100 : 0"
            :color="item.color"
            height="8"
            rounded
            class="custom-progress"
          ></v-progress-linear>
        </div>
      </div>

      <v-divider class="my-5"></v-divider>

      <!-- Stats Footer -->
      <div class="stats-footer">
        <v-row>
          <v-col cols="6">
            <div class="stat-card">
              <div class="stat-icon-wrapper gradient-primary mb-3">
                <v-icon icon="mdi-bug-outline" color="white" size="24"></v-icon>
              </div>
              <div class="stat-value">{{ alerts.length }}</div>
              <div class="stat-label">Total Vulnerabilities</div>
            </div>
          </v-col>
          <v-col cols="6">
            <div class="stat-card">
              <div class="stat-icon-wrapper gradient-secondary mb-3">
                <v-icon icon="mdi-radar" color="white" size="24"></v-icon>
              </div>
              <div class="stat-value">{{ scanType }}</div>
              <div class="stat-label">Scan Type</div>
            </div>
          </v-col>
        </v-row>
      </div>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.progress-card {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 20px;
  transition: all 0.3s ease;
}

.progress-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
}

.glass-card {
  background: rgba(255, 255, 255, 0.9) !important;
}

.severity-badge {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.severity-high {
  background: #ef4444;
}

.severity-medium {
  background: #f59e0b;
}

.severity-low {
  background: #10b981;
}

.severity-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #334155;
}

.severity-value {
  font-weight: 500;
  font-size: 0.875rem;
  color: #64748b;
}

.custom-progress {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.gradient-secondary {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>