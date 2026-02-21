<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useScanStore } from '@/stores/scanStore';
import reportService from '@/services/reportService';
import { storeToRefs } from 'pinia';

const route = useRoute();
const router = useRouter();
const scanStore = useScanStore();
const { scanResults, isLoadingResults } = storeToRefs(scanStore);
const scanId = route.params.id as string;

const reportLoading = ref(false);
const downloadLoading = ref(false);
const reportId = ref<string | null>(null);
const errorMsg = ref('');
const successMsg = ref('');

onMounted(async () => {
  try {
    await scanStore.fetchScanResults(scanId);
  } catch (error) {
    errorMsg.value = 'Failed to load scan details';
  }
});

const generateReport = async () => {
  reportLoading.value = true;
  errorMsg.value = '';
  try {
    const response = await reportService.generateReport(scanId);
    reportId.value = response.report_id || response.id;
    successMsg.value = 'Report generated successfully!';
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || 'Failed to generate report';
  } finally {
    reportLoading.value = false;
  }
};

const downloadReport = async () => {
  if (!reportId.value) {
    errorMsg.value = 'Please generate a report first';
    return;
  }
  downloadLoading.value = true;
  try {
    const blob = await reportService.downloadReport(reportId.value);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${scanId}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || 'Failed to download report';
  } finally {
    downloadLoading.value = false;
  }
};

const goBack = () => {
  router.push('/scanner/history');
};

const getSeverityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'high': return 'red-accent-3';
    case 'medium': return 'orange-accent-3';
    case 'low': return 'blue-grey';
    default: return 'grey';
  }
};
</script>

<template>
  <div class="scan-details-container">
    <v-container>
      <!-- Breadcrumb / Back Navigation -->
      <div class="d-flex align-center mb-6">
        <v-btn icon="mdi-arrow-left" variant="text" @click="goBack" class="mr-2"></v-btn>
        <div>
           <div class="text-overline text-grey-darken-1">Scan History</div>
           <h1 class="text-h4 font-weight-bold text-slate-800">Scan Details</h1>
        </div>
        <v-spacer></v-spacer>
        <!-- Actions -->
        <v-btn prepend-icon="mdi-file-chart" color="primary" class="mr-2" @click="generateReport" :loading="reportLoading">Generate Report</v-btn>
        <v-btn prepend-icon="mdi-download" variant="outlined" color="secondary" @click="downloadReport" :loading="downloadLoading" :disabled="!reportId">Download PDF</v-btn>
      </div>

      <!-- Alerts -->
      <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="errorMsg = ''">{{ errorMsg }}</v-alert>
      <v-alert v-if="successMsg" type="success" variant="tonal" density="compact" class="mb-4" closable @click:close="successMsg = ''">{{ successMsg }}</v-alert>

      <!-- Loading -->
      <div v-if="isLoadingResults" class="text-center py-16">
        <v-progress-circular indeterminate size="64" width="6" color="primary"></v-progress-circular>
        <div class="text-body-1 mt-4 text-grey">Loading scan details...</div>
      </div>

      <template v-else-if="scanResults">
        <!-- Overview Card -->
        <v-card class="glass-card mb-6" elevation="0">
          <v-card-text>
              <v-row>
                  <v-col cols="12" md="6">
                      <div class="text-caption text-grey">Target URL</div>
                      <div class="text-h6">{{ scanResults.target || scanResults.url || 'N/A' }}</div>
                  </v-col>
                  <v-col cols="6" md="3">
                       <div class="text-caption text-grey">Status</div>
                      <v-chip color="success" size="small">{{ scanResults.status || 'Completed' }}</v-chip>
                  </v-col>
                   <v-col cols="6" md="3">
                       <div class="text-caption text-grey">Scan Date</div>
                      <div class="text-body-1">{{ scanResults.created_at ? new Date(scanResults.created_at).toLocaleString() : 'N/A' }}</div>
                  </v-col>
              </v-row>
          </v-card-text>
        </v-card>

        <!-- Vulnerabilities List -->
        <h2 class="text-h5 font-weight-bold text-slate-800 mb-4">Vulnerabilities Found</h2>
        
        <v-row v-if="scanResults && scanResults.length > 0">
            <v-col v-for="(vuln, index) in scanResults" :key="index" cols="12">
                <v-card class="glass-card vulnerability-card pa-2" elevation="0">
                    <div class="d-flex align-center">
                        <div class="severity-indicator mr-4" :class="getSeverityColor(vuln.risk || vuln.severity || '')"></div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-space-between align-center mb-1">
                                <h3 class="text-h6 font-weight-medium">{{ vuln.alert || vuln.title }}</h3>
                                <v-chip :color="getSeverityColor(vuln.risk || vuln.severity || '')" size="small" variant="flat">{{ vuln.risk || vuln.severity }}</v-chip>
                            </div>
                            <p class="text-body-2 text-grey-darken-1 mb-0">{{ vuln.description }}</p>
                            <div v-if="vuln.url" class="text-caption text-grey mt-1">URL: {{ vuln.url }}</div>
                        </div>
                    </div>
                </v-card>
            </v-col>
        </v-row>
        <div v-else class="text-center py-8 text-medium-emphasis">
          <v-icon icon="mdi-shield-check" size="48" color="success" class="mb-2"></v-icon>
          <div>No vulnerabilities found in this scan</div>
        </div>
      </template>

      <v-alert v-else type="info" title="No Data" text="No scan results available for this scan."></v-alert>

    </v-container>
  </div>
</template>

<style scoped>
.scan-details-container {
  padding-top: 24px;
  min-height: 100vh;
  background: #f8fafc;
}

.glass-card {
  background: white !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
}

.vulnerability-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.vulnerability-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.severity-indicator {
    width: 6px;
    height: 40px;
    border-radius: 3px;
}
.severity-indicator.red-accent-3 { background-color: #ff1744; }
.severity-indicator.orange-accent-3 { background-color: #ff9100; }
.severity-indicator.blue-grey { background-color: #607d8b; }
.severity-indicator.grey { background-color: #9e9e9e; }
</style>
