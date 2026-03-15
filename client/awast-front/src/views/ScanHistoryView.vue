<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';
import reportService from '@/services/reportService';

const search = ref('');
const router = useRouter();
const scanStore = useScanStore();
const { scanHistory, isLoadingHistory } = storeToRefs(scanStore);

const deleteDialog = ref(false);
const scanToDelete = ref<string | null>(null);
const isDeleting = ref(false);
const deleteError = ref<string | null>(null);

const clearAllDialog = ref(false);
const isClearing = ref(false);
const clearError = ref<string | null>(null);

const reportDownloadingId = ref<string | null>(null);
const reportError = ref<string | null>(null);
const reportSnackbar = ref({ show: false, text: '', color: 'success' as 'success' | 'error' });

const headers = [
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Target URL', key: 'target', sortable: true },
  { title: 'Date', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const },
];

onMounted(async () => {
  await scanStore.fetchScanHistory();
});

const totalScans = computed(() => scanHistory.value.length);

const getStatusColor = (status: string) => {
  switch (status) {
    case 'done': return 'success';
    case 'error': return 'error';
    case 'running': return 'info';
    case 'pending': return 'warning';
    case 'stopped': return 'grey';
    default: return 'grey';
  }
};

const viewDetails = (scanId: string) => {
  router.push(`/scanner/${scanId}`);
};

const initiateNewScan = () => {
  router.push('/scanner');
};

const confirmDelete = (scanId: string) => {
  scanToDelete.value = scanId;
  deleteError.value = null;
  deleteDialog.value = true;
};

const cancelDelete = () => {
  deleteDialog.value = false;
  scanToDelete.value = null;
  deleteError.value = null;
};

const executeDelete = async () => {
  if (!scanToDelete.value) return;
  isDeleting.value = true;
  deleteError.value = null;
  try {
    await scanStore.deleteScan(scanToDelete.value);
    deleteDialog.value = false;
    scanToDelete.value = null;
  } catch {
    deleteError.value = 'Failed to delete scan. Please try again.';
  } finally {
    isDeleting.value = false;
  }
};

const executeClearAll = async () => {
  isClearing.value = true;
  clearError.value = null;
  try {
    await scanStore.clearAllScans();
    clearAllDialog.value = false;
  } catch {
    clearError.value = 'Failed to clear history. Please try again.';
  } finally {
    isClearing.value = false;
  }
};

const generateAndDownloadReport = async (scanId: string) => {
  reportDownloadingId.value = scanId;
  reportError.value = null;
  reportSnackbar.value.show = false;
  try {
    const data = await reportService.generateReport(scanId) as { report_id: string };
    const reportId = data?.report_id;
    if (!reportId) {
      throw new Error('No report_id returned');
    }
    const blob = await reportService.downloadReport(reportId);
    const url = URL.createObjectURL(blob as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vulnerability_report_${scanId.slice(0, 8)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    reportSnackbar.value = { show: true, text: 'Report generated and downloaded.', color: 'success' };
  } catch {
    reportError.value = 'Failed to generate or download report. Please try again.';
    reportSnackbar.value = { show: true, text: reportError.value, color: 'error' };
  } finally {
    reportDownloadingId.value = null;
  }
};
</script>

<template>
  <div class="scan-history-container">
    <div class="header-section mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold text-slate-800 mb-2">Scan History</h1>
        <p class="text-subtitle-1 text-grey-darken-1">Monitor and manage your security assessment logs.</p>
      </div>
      <div class="d-flex ga-3">
        <v-btn
          color="error"
          prepend-icon="mdi-delete-sweep-outline"
          size="large"
          variant="tonal"
          class="text-none"
          :disabled="totalScans === 0"
          @click="clearAllDialog = true"
        >
          Clear All
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          size="large"
          variant="elevated"
          class="text-none glow-button"
          @click="initiateNewScan"
        >
          New Scan
        </v-btn>
      </div>
    </div>

    <!-- Stats Cards Row -->
    <v-row class="mb-6">
      <v-col cols="12" md="4">
        <v-card class="glass-card h-100" elevation="0">
          <v-card-text class="d-flex align-center">
            <v-avatar color="blue-darken-3" size="48" class="mr-4">
              <v-icon icon="mdi-shield-check" color="white"></v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-grey">Total Scans</div>
              <div class="text-h5 font-weight-bold text-black">{{ totalScans }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="glass-table-card rounded-lg" elevation="0">
      <v-data-table
        :headers="headers"
        :items="scanHistory"
        :search="search"
        :loading="isLoadingHistory"
        :sort-by="[{ key: 'created_at', order: 'desc' }]"
        class="bg-transparent"
        hover
      >
        <template v-slot:top>
          <v-toolbar flat color="transparent" class="px-4 py-2">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Search scans..."
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="search-bar"
              bg-color="white"
            ></v-text-field>
            <v-spacer></v-spacer>
          </v-toolbar>
        </template>

        <!-- Status Column -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            class="font-weight-medium"
            variant="flat"
          >
            {{ item.status }}
          </v-chip>
        </template>

        <!-- Date Column -->
        <template v-slot:item.created_at="{ item }">
          {{ item.created_at ? new Date(item.created_at).toLocaleString() : '-' }}
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon="mdi-file-pdf-box"
            variant="text"
            size="small"
            color="primary"
            :loading="reportDownloadingId === item.scan_id"
            :disabled="!!reportDownloadingId"
            title="Generate and download report"
            @click="generateAndDownloadReport(item.scan_id)"
          ></v-btn>
          <v-btn icon="mdi-file-document-outline" variant="text" size="small" color="primary" @click="viewDetails(item.scan_id)"></v-btn>
          <v-btn icon="mdi-trash-can-outline" variant="text" size="small" color="error" @click="confirmDelete(item.scan_id)"></v-btn>
        </template>

        <!-- Empty State -->
        <template v-slot:no-data>
          <div class="text-center py-8">
            <v-icon icon="mdi-radar" size="48" color="grey" class="mb-2"></v-icon>
            <div class="text-medium-emphasis">No scan history found</div>
          </div>
        </template>
      </v-data-table>
    </v-card>
  </div>

  <!-- Delete Confirmation Dialog -->
  <v-dialog v-model="deleteDialog" max-width="420" persistent>
    <v-card class="rounded-lg" elevation="4">
      <v-card-title class="d-flex align-center pt-5 px-6">
        <v-icon icon="mdi-alert-circle-outline" color="error" class="mr-2"></v-icon>
        Delete Scan
      </v-card-title>
      <v-card-text class="px-6 pb-2">
        <p class="text-body-1 text-grey-darken-2">
          Are you sure you want to delete this scan? All associated vulnerabilities will be permanently removed.
        </p>
        <v-alert v-if="deleteError" type="error" variant="tonal" density="compact" class="mt-3">
          {{ deleteError }}
        </v-alert>
      </v-card-text>
      <v-card-actions class="px-6 pb-5 pt-2">
        <v-spacer></v-spacer>
        <v-btn variant="text" color="grey" class="text-none" @click="cancelDelete" :disabled="isDeleting">Cancel</v-btn>
        <v-btn variant="elevated" color="error" class="text-none" :loading="isDeleting" @click="executeDelete">Delete</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Clear All Confirmation Dialog -->
  <v-dialog v-model="clearAllDialog" max-width="440" persistent>
    <v-card class="rounded-lg" elevation="4">
      <v-card-title class="d-flex align-center pt-5 px-6">
        <v-icon icon="mdi-delete-sweep-outline" color="error" class="mr-2"></v-icon>
        Clear All History
      </v-card-title>
      <v-card-text class="px-6 pb-2">
        <p class="text-body-1 text-grey-darken-2">
          This will permanently delete <strong>all {{ totalScans }} scan(s)</strong> and their associated vulnerabilities. This action cannot be undone.
        </p>
        <v-alert v-if="clearError" type="error" variant="tonal" density="compact" class="mt-3">
          {{ clearError }}
        </v-alert>
      </v-card-text>
      <v-card-actions class="px-6 pb-5 pt-2">
        <v-spacer></v-spacer>
        <v-btn variant="text" color="grey" class="text-none" @click="clearAllDialog = false" :disabled="isClearing">Cancel</v-btn>
        <v-btn variant="elevated" color="error" class="text-none" :loading="isClearing" @click="executeClearAll">Clear All</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Report download snackbar -->
  <v-snackbar v-model="reportSnackbar.show" :color="reportSnackbar.color" :timeout="reportSnackbar.color === 'error' ? 5000 : 3000" location="bottom right">
    {{ reportSnackbar.text }}
  </v-snackbar>
</template>

<style scoped>
.scan-history-container {
  padding: 24px;
  min-height: 100vh;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.glass-card {
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.1);
}

.glass-table-card {
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden; 
}

.glow-button {
  box-shadow: 0 4px 15px rgba(var(--v-theme-primary), 0.3);
  transition: box-shadow 0.2s;
}

.glow-button:hover {
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.4);
}

.search-bar {
  max-width: 300px;
}

/* Custom Table Styling for Light Mode */
:deep(.v-data-table) {
  background: transparent !important;
  color: #334155;
}

:deep(.v-data-table__tr:hover) {
  background: rgba(0, 0, 0, 0.02) !important;
}

:deep(.v-data-table-header__content) {
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}
</style>
