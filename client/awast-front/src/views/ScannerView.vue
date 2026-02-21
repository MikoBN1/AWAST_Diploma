<script setup lang="ts">
import { ref, onUnmounted, onMounted } from "vue";
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';
import ScanInfoBlocks from "../components/scanner/ScanInfoBlocks.vue";
import ScanVulnerabilitiesProgress from "../components/scanner/ScanVulnerabilitiesProgress.vue";
import ScanVulnerabilitiyList from "../components/scanner/ScanVulnerabilitiyList.vue";

const scanStore = useScanStore();
const { isScanning, scanProgress } = storeToRefs(scanStore);

const model = ref(true);
const visible = ref(false);
const targetUrl = ref('');
const username = ref('');
const password = ref('');
const errorMsg = ref('');
const successMsg = ref('');
const scanPhase = ref(''); // 'scan' | ''

const startScan = async () => {
  if (!targetUrl.value) {
    errorMsg.value = 'Please enter a target URL';
    return;
  }
  errorMsg.value = '';
  successMsg.value = '';
  
  try {
    scanPhase.value = 'scan';
    await scanStore.startScan(targetUrl.value);
    
    if (!scanStore.activeScanId) return;
    
    // Connect to the WebSocket for live updates
    scanStore.connectToScanSocket(
      scanStore.activeScanId,
      () => {
        // On Complete
        scanPhase.value = '';
        successMsg.value = 'Scan completed successfully!';
      },
      (err) => {
        // On Error
        errorMsg.value = `Scan error: ${err}`;
        scanPhase.value = '';
      }
    );
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || 'Failed to start scan';
    scanPhase.value = '';
  }
};

onUnmounted(() => {
  if (scanStore.wsConnection) {
    scanStore.wsConnection.close();
  }
});
</script>

<template>
  <div class="scanner-container">
    <!-- Hero Header Section -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="icon-badge mb-4">
          <v-icon icon="mdi-shield-search" size="48" color="primary"></v-icon>
        </div>
        <h1 class="text-h3 font-weight-bold text-slate-800 mb-3">Vulnerability Scanner</h1>
        <p class="text-subtitle-1 text-white mb-0">
          Identify security vulnerabilities in your web applications with advanced automated scanning
        </p>
      </div>
    </div>

    <!-- Main Scan Configuration Card -->
    <v-container class="px-4">
      <v-row justify="center" class="mb-8">
        <v-col cols="12" md="8" lg="6">
          <v-card class="scan-card glass-card" elevation="0">
            <v-card-text class="pa-8">
              <!-- Card Header -->
              <div class="card-header mb-6">
                <div class="icon-wrapper gradient-primary mb-4">
                  <v-icon icon="mdi-web" size="32" color="white"></v-icon>
                </div>
                <h2 class="text-h5 font-weight-bold text-slate-800 mb-2">Configure Your Scan</h2>
                <p class="text-body-2 text-grey-darken-1">
                  Enter your target URL and optional authentication credentials
                </p>
              </div>

              <!-- Alerts -->
              <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="errorMsg = ''">{{ errorMsg }}</v-alert>
              <v-alert v-if="successMsg" type="success" variant="tonal" density="compact" class="mb-4" closable @click:close="successMsg = ''">{{ successMsg }}</v-alert>

              <!-- Scan Progress -->
              <v-alert v-if="isScanning" type="info" variant="tonal" density="compact" class="mb-4">
                <div class="d-flex align-center">
                  <v-progress-circular indeterminate size="20" width="2" class="mr-3"></v-progress-circular>
                  <span>Active scanning in progress... {{ scanProgress }}% complete</span>
                </div>
              </v-alert>

              <!-- URL Input -->
              <div class="mb-5">
                <label class="input-label mb-2">Target URL</label>
                <v-text-field
                  v-model="targetUrl"
                  density="comfortable"
                  placeholder="https://example.com"
                  prepend-inner-icon="mdi-link-variant"
                  variant="outlined"
                  color="primary"
                  bg-color="white"
                  class="modern-input"
                  hide-details
                  :disabled="isScanning"
                ></v-text-field>
              </div>

              <!-- Authentication Toggle -->
              <div class="auth-section mb-5">
                <v-card class="toggle-card pa-4" elevation="0">
                  <div class="d-flex align-center justify-space-between">
                    <div class="d-flex align-center">
                      <v-icon icon="mdi-account-lock" color="primary" class="mr-3"></v-icon>
                      <div>
                        <div class="font-weight-medium text-slate-800">Enable Authentication</div>
                        <div class="text-caption text-grey-darken-1">Scan authenticated areas of your application</div>
                      </div>
                    </div>
                    <v-switch
                      v-model="model"
                      hide-details
                      color="primary"
                      inset
                      class="ml-4"
                      :disabled="isScanning"
                    ></v-switch>
                  </div>
                </v-card>
              </div>

              <!-- Credentials Section -->
              <div v-show="model" class="credentials-section">
                  <div class="mb-4">
                    <label class="input-label mb-2">Username or Email</label>
                    <v-text-field
                      v-model="username"
                      density="comfortable"
                      placeholder="Enter username or email"
                      prepend-inner-icon="mdi-account-outline"
                      variant="outlined"
                      color="primary"
                      bg-color="white"
                      class="modern-input"
                      hide-details
                      :disabled="isScanning"
                    ></v-text-field>
                  </div>

                  <div class="mb-6">
                    <label class="input-label mb-2">Password</label>
                    <v-text-field
                      v-model="password"
                      :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
                      :type="visible ? 'text' : 'password'"
                      density="comfortable"
                      placeholder="Enter password"
                      prepend-inner-icon="mdi-lock-outline"
                      variant="outlined"
                      color="primary"
                      bg-color="white"
                      class="modern-input"
                      @click:append-inner="visible = !visible"
                      hide-details
                      :disabled="isScanning"
                    ></v-text-field>
                  </div>
                </div>

              <!-- Action Button -->
              <v-btn
                block
                size="x-large"
                color="primary"
                variant="elevated"
                class="text-none font-weight-bold glow-button"
                prepend-icon="mdi-radar"
                @click="startScan"
                :loading="isScanning"
                :disabled="isScanning"
              >
                {{ isScanning ? 'Scanning...' : 'Start Security Scan' }}
              </v-btn>

              <!-- Info Footer -->
              <div class="info-footer mt-6 pa-4">
                <v-icon icon="mdi-information-outline" size="20" color="primary" class="mr-2"></v-icon>
                <span class="text-caption text-grey-darken-1">
                  Scans typically complete in 5-30 minutes depending on application size
                </span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Vulnerabilities Progress -->
      <v-row class="mb-8">
        <v-col cols="12">
          <ScanVulnerabilitiesProgress/>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <ScanInfoBlocks/>
        </v-col>
      </v-row>

      <!-- Vulnerabilities List -->
      <v-row class="mb-8">
        <ScanVulnerabilitiyList/>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.scanner-container {
  min-height: 100vh;
  padding-bottom: 48px;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 80px 24px 100px;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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

.icon-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 24px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  animation: float 3s ease-in-out infinite;
  will-change: transform;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

.hero-section h1 {
  color: white;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.hero-section p {
  color: rgba(255, 255, 255, 0.95);
  font-size: 1.125rem;
}

/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 24px;
  position: relative;
  z-index: 2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  will-change: transform;
  transform: translateZ(0);
}

.glass-card:hover {
  transform: translateY(-4px) translateZ(0);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

/* Card Header */
.card-header {
  text-align: center;
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Input Styling */
.input-label {
  display: block;
  font-weight: 600;
  font-size: 0.875rem;
  color: #334155;
  letter-spacing: 0.025em;
}

.modern-input {
  border-radius: 12px;
}

:deep(.modern-input .v-field) {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

:deep(.modern-input .v-field:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

:deep(.modern-input .v-field--focused) {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
}

/* Toggle Card */
.toggle-card {
  background: #f8fafc !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.toggle-card:hover {
  background: #f1f5f9 !important;
  border-color: rgba(102, 126, 234, 0.2);
}

/* Credentials Section */
.credentials-section {
  padding: 16px;
  background: rgba(102, 126, 234, 0.03);
  border-radius: 16px;
  border: 1px dashed rgba(102, 126, 234, 0.2);
  margin-bottom: 24px;
  will-change: auto;
}

/* Glow Button */
.glow-button {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  border-radius: 12px;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.glow-button:hover {
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

/* Info Footer */
.info-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}
</style>