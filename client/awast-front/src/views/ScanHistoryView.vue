<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';

const search = ref('');
const router = useRouter();
const scanStore = useScanStore();
const { scanHistory, isLoadingHistory } = storeToRefs(scanStore);

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
    case 'finished': return 'success';
    case 'error': return 'error';
    case 'running': return 'info';
    case 'pending': return 'warning';
    default: return 'grey';
  }
};

const viewDetails = (scanId: string) => {
  router.push(`/scanner/history/${scanId}`);
};

const initiateNewScan = () => {
  router.push('/scanner');
};
</script>

<template>
  <div class="scan-history-container">
    <div class="header-section mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold text-slate-800 mb-2">Scan History</h1>
        <p class="text-subtitle-1 text-grey-darken-1">Monitor and manage your security assessment logs.</p>
      </div>
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
          <v-btn icon="mdi-file-document-outline" variant="text" size="small" color="primary" @click="viewDetails(item.scan_id)"></v-btn>
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
