<script setup lang="ts">
import { useRouter } from 'vue-router';
import reportService from '@/services/reportService';
import { ref } from 'vue';
import { useScanStore } from '@/stores/scanStore';

const router = useRouter();
const scanStore = useScanStore();

const props = defineProps<{
  scans: any[];
}>();

const reportLoading = ref<string | null>(null);
const deleteDialog = ref(false);
const scanToDelete = ref<string | null>(null);
const isDeleting = ref(false);

const tableHeaders = ['Target', 'Status', 'Date', 'Report', ''];

function determineStatus(status: string) {
    switch (status) {
      case 'none': return 'Generate'
      case 'done': return 'Download'
      case 'failed': return 'Failed, Try Again'
      default: return 'Pending'
    }
}

const handleReport = async (scan: any) => {
  reportLoading.value = scan.scan_id;
  try {
    if (scan.report_status === 'done' && scan.report_id) {
      const blob = await reportService.downloadReport(scan.report_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${scan.scan_id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      await reportService.generateReport(scan.scan_id);
    }
  } catch (error) {
    console.error('Report action failed', error);
  } finally {
    reportLoading.value = null;
  }
};

const viewScan = (scanId: string) => {
  router.push(`/scanner/${scanId}`);
};

const viewAll = () => {
  router.push('/scanner/history');
};

const confirmDelete = (scanId: string) => {
  scanToDelete.value = scanId;
  deleteDialog.value = true;
};

const cancelDelete = () => {
  deleteDialog.value = false;
  scanToDelete.value = null;
};

const executeDelete = async () => {
  if (!scanToDelete.value) return;
  isDeleting.value = true;
  try {
    await scanStore.deleteScan(scanToDelete.value);
    deleteDialog.value = false;
    scanToDelete.value = null;
  } catch (error) {
    console.error('Failed to delete scan', error);
  } finally {
    isDeleting.value = false;
  }
};
</script>

<template>
<v-card class="rounded-xl border-thin" elevation="0">
  <v-card-item class="px-6 pt-6">
    <div class="d-flex justify-space-between align-center">
        <v-card-title class="font-weight-bold">Recent Scans</v-card-title>
        <v-btn variant="text" size="small" color="primary" @click="viewAll">View All</v-btn>
    </div>
  </v-card-item>
  <v-card-text class="px-0">
    <v-table class="scans-table" v-if="scans.length > 0">
      <thead>
        <tr>
          <th v-for="(header, i) in tableHeaders" :key="i">
            {{header}}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="scan in scans.slice(0, 5)" :key="scan.scan_id" class="scan-row">
          <td class="font-weight-medium text-body-2">{{scan.target}}</td>
          <td>
             <v-chip
                :color="scan.status === 'done' ? 'success' : scan.status === 'error' ? 'error' : scan.status === 'stopped' ? 'grey' : 'warning'"
                size="x-small"
                class="font-weight-bold text-uppercase"
                label
             >
              {{scan.status}}
             </v-chip>
          </td>
          <td class="text-caption text-grey">{{ new Date(scan.created_at).toLocaleDateString() }}</td>
          <td>
            <div v-if="scan.report_status && scan.report_status !== 'none'" class="d-flex align-center">
                 <v-btn
                    v-if="scan.report_status === 'done'"
                    density="compact"
                    variant="tonal"
                    color="primary"
                    icon="mdi-download"
                    size="small"
                    class="mr-2"
                    :loading="reportLoading === scan.scan_id"
                    @click="handleReport(scan)"
                 ></v-btn>
                 <span class="text-caption">{{ determineStatus(scan.report_status) }}</span>
            </div>
             <span v-else class="text-caption text-grey-lighten-1">No Report</span>
          </td>
          <td>
            <v-btn icon="mdi-chevron-right" variant="text" density="comfortable" color="grey" @click="viewScan(scan.scan_id)"></v-btn>
            <v-btn icon="mdi-trash-can-outline" variant="text" density="comfortable" color="error" @click="confirmDelete(scan.scan_id)"></v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
    <div v-else class="text-center py-8 text-medium-emphasis">
      <v-icon icon="mdi-radar" size="48" class="mb-2"></v-icon>
      <div>No scans yet. Start your first scan!</div>
    </div>
  </v-card-text>
</v-card>

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
    </v-card-text>
    <v-card-actions class="px-6 pb-5 pt-2">
      <v-spacer></v-spacer>
      <v-btn variant="text" color="grey" class="text-none" @click="cancelDelete" :disabled="isDeleting">Cancel</v-btn>
      <v-btn variant="elevated" color="error" class="text-none" :loading="isDeleting" @click="executeDelete">Delete</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
</template>

<style scoped>
.scan-row {
  transition: background-color 0.2s;
}
.scan-row:hover {
  background-color: #f8fafc !important;
}
.border-thin {
   border: 1px solid rgba(0,0,0,0.05);
}
</style>