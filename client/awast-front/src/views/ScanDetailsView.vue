<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Mock data logic
const route = useRoute();
const router = useRouter();
const scanId = route.params.id as string;

const scanDetails = ref({
  id: scanId,
  target: 'https://example-vulnerable-site.com',
  status: 'Completed',
  date: '2023-10-27 14:30',
  duration: '45m 12s',
  vulnerabilities: [
    { title: 'SQL Injection', severity: 'High', description: 'Possible SQL injection in id parameter' },
    { title: 'XSS Reflected', severity: 'Medium', description: 'Reflected XSS in search query' },
    { title: 'Missing Headers', severity: 'Low', description: 'X-Frame-Options header missing' },
  ]
});

const generateReport = () => {
  // TODO: Implement /report/new API call
  console.log('Generating report for', scanId);
};

const downloadReport = () => {
    // TODO: Implement /report/download API call
    console.log('Downloading report for', scanId);
}

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
        <v-btn prepend-icon="mdi-file-chart" color="primary" class="mr-2" @click="generateReport">Generate Report</v-btn>
        <v-btn prepend-icon="mdi-download" variant="outlined" color="secondary" @click="downloadReport">Download PDF</v-btn>
      </div>

       <!-- Overview Card -->
      <v-card class="glass-card mb-6" elevation="0">
        <v-card-text>
            <v-row>
                <v-col cols="12" md="6">
                    <div class="text-caption text-grey">Target URL</div>
                    <div class="text-h6">{{ scanDetails.target }}</div>
                </v-col>
                <v-col cols="6" md="3">
                     <div class="text-caption text-grey">Status</div>
                    <v-chip color="success" size="small">{{ scanDetails.status }}</v-chip>
                </v-col>
                 <v-col cols="6" md="3">
                     <div class="text-caption text-grey">Scan Date</div>
                    <div class="text-body-1">{{ scanDetails.date }}</div>
                </v-col>
            </v-row>
        </v-card-text>
      </v-card>

      <!-- Vulnerabilities List -->
      <h2 class="text-h5 font-weight-bold text-slate-800 mb-4">Vulnerabilities Found</h2>
      
      <v-row>
          <v-col v-for="(vuln, index) in scanDetails.vulnerabilities" :key="index" cols="12">
              <v-card class="glass-card vulnerability-card pa-2" elevation="0">
                  <div class="d-flex align-center">
                      <div class="severity-indicator mr-4" :class="getSeverityColor(vuln.severity)"></div>
                      <div class="flex-grow-1">
                          <div class="d-flex justify-space-between align-center mb-1">
                              <h3 class="text-h6 font-weight-medium">{{ vuln.title }}</h3>
                              <v-chip :color="getSeverityColor(vuln.severity)" size="small" variant="flat">{{ vuln.severity }}</v-chip>
                          </div>
                          <p class="text-body-2 text-grey-darken-1 mb-0">{{ vuln.description }}</p>
                      </div>
                  </div>
              </v-card>
          </v-col>
      </v-row>

    </v-container>
  </div>
</template>

<style scoped>
.scan-details-container {
  padding-top: 24px;
  min-height: 100vh;
  background: #f8fafc; /* Light background */
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
