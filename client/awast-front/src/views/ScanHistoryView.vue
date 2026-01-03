<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// Mock Data for UI Design
const search = ref('');
const router = useRouter();
const headers = [
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Target URL', key: 'target', sortable: true },
  { title: 'Date', key: 'date', sortable: true },
  { title: 'Duration', key: 'duration', sortable: true },
  { title: 'Risks Found', key: 'risks', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const },
];

const historyItems = ref([
  {
    id: '1',
    status: 'Completed',
    target: 'https://example-vulnerable-site.com',
    date: '2023-10-27 14:30',
    duration: '45m 12s',
    risks: { high: 2, medium: 5, low: 12 },
  },
  {
    id: '2',
    status: 'Failed',
    target: 'http://internal-test.local',
    date: '2023-10-26 09:15',
    duration: '2m 05s',
    risks: { high: 0, medium: 0, low: 0 },
  },
  {
    id: '3',
    status: 'In Progress',
    target: 'https://staging.app.com',
    date: '2023-10-27 15:00',
    duration: 'Running...',
    risks: { high: 1, medium: 2, low: 0 },
  },
  {
    id: '4',
    status: 'Completed',
    target: 'https://production-api.com',
    date: '2023-10-25 11:20',
    duration: '1h 15m',
    risks: { high: 0, medium: 1, low: 4 },
  },
]);

const getStatusColor = (status: string) => {
  switch (status) {
    case 'Completed': return 'success';
    case 'Failed': return 'error';
    case 'In Progress': return 'info';
    default: return 'grey';
  }
};

const initiateNewScan = () => {
  router.push('/scanner');
}
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
              <div class="text-h5 font-weight-bold text-black">124</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="glass-card h-100" elevation="0">
          <v-card-text class="d-flex align-center">
             <v-avatar color="red-darken-3" size="48" class="mr-4">
              <v-icon icon="mdi-alert-circle" color="white"></v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-grey">High Risk Found</div>
              <div class="text-h5 font-weight-bold text-black">12</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="glass-card h-100" elevation="0">
          <v-card-text class="d-flex align-center">
             <v-avatar color="green-darken-3" size="48" class="mr-4">
              <v-icon icon="mdi-clock-check" color="white"></v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-grey">Avg Duration</div>
              <div class="text-h5 font-weight-bold text-black">34m</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="glass-table-card rounded-lg" elevation="0">
      <v-data-table
        :headers="headers"
        :items="historyItems"
        :search="search"
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
            <v-btn variant="text" color="grey-darken-2" size="small" prepend-icon="mdi-filter-variant">Filter</v-btn>
            <v-btn variant="text" color="grey-darken-2" size="small" prepend-icon="mdi-export">Export</v-btn>
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

        <!-- Risks Column -->
        <template v-slot:item.risks="{ item }">
          <div class="d-flex align-center gap-2">
            <v-tooltip location="top" text="High Risk">
              <template v-slot:activator="{ props }">
                <v-badge v-bind="props" :content="item.risks.high" color="red-accent-3" inline v-if="item.risks.high > 0" class="mr-2"></v-badge>
              </template>
            </v-tooltip>
             <v-tooltip location="top" text="Medium Risk">
              <template v-slot:activator="{ props }">
                 <v-badge v-bind="props" :content="item.risks.medium" color="orange-accent-3" inline v-if="item.risks.medium > 0" class="mr-2"></v-badge>
              </template>
            </v-tooltip>
             <v-tooltip location="top" text="Low Risk">
              <template v-slot:activator="{ props }">
                <v-badge v-bind="props" :content="item.risks.low" color="blue-grey" inline v-if="item.risks.low > 0"></v-badge>
              </template>
            </v-tooltip>
            <span v-if="item.risks.high === 0 && item.risks.medium === 0 && item.risks.low === 0" class="text-caption text-grey">Safe</span>
          </div>
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-file-document-outline" variant="text" size="small" color="primary"></v-btn>
          <v-btn icon="mdi-delete-outline" variant="text" size="small" color="grey"></v-btn>
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
