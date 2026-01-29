<script setup lang="ts">
const tableHeaders = ['Target', 'Status', 'Date', 'Report', 'View']
const scans: Scan[] = [
  {
    scan_id: "1",
    target: "example.com",
    created_at: "2025-01-01T10:00:00Z",
    status: "pending",
    report_id: null,
    report_status: "none"
  },
  {
    scan_id: "2",
    target: "api.example.com",
    created_at: "2025-01-02T11:00:00Z",
    status: "running",
    report_id: null,
    report_status: "none"
  },
  {
    scan_id: "3",
    target: "service.local",
    created_at: "2025-01-03T12:00:00Z",
    status: "finished",
    report_id: "rep-3",
    report_status: "done"
  },
  {
    scan_id: "4",
    target: "dev.example.net",
    created_at: "2025-01-04T13:00:00Z",
    status: "error",
    report_id: null,
    report_status: "failed"
  },
  {
    scan_id: "5",
    target: "staging.example.io",
    created_at: "2025-01-05T14:00:00Z",
    status: "finished",
    report_id: "rep-5",
    report_status: "done"
  }
];

function determineStatus(status: string) {
    switch (status) {
      case 'none': return 'Generate'
      case 'done': return 'Download'
      case 'failed': return 'Failed, Try Again'
      default: return 'Pending'
    }
}
interface Scan{
  scan_id: string
  target: string
  created_at: string
  status: string
  report_id: string | null
  report_status: string
}
</script>

<template>
<v-card class="rounded-xl border-thin" elevation="0">
  <v-card-item class="px-6 pt-6">
    <div class="d-flex justify-space-between align-center">
        <v-card-title class="font-weight-bold">Recent Scans</v-card-title>
        <v-btn variant="text" size="small" color="primary">View All</v-btn>
    </div>
  </v-card-item>
  <v-card-text class="px-0">
    <v-table class="scans-table">
      <thead>
        <tr>
          <th v-for="(header, i) in tableHeaders" :key="i">
            {{header}}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="scan in scans" :key="scan.scan_id" class="scan-row">
          <td class="font-weight-medium text-body-2">{{scan.target}}</td>
          <td>
             <v-chip
                :color="scan.status === 'finished' ? 'success' : scan.status === 'error' ? 'error' : 'warning'"
                size="x-small"
                class="font-weight-bold text-uppercase"
                label
             >
              {{scan.status}}
             </v-chip>
          </td>
          <td class="text-caption text-grey">{{ new Date(scan.created_at).toLocaleDateString() }}</td>
          <td>
            <div v-if="scan.report_status !== 'none'" class="d-flex align-center">
                 <v-btn
                    v-if="scan.report_status === 'done'"
                    density="compact"
                    variant="tonal"
                    color="primary"
                    icon="mdi-download"
                    size="small"
                    class="mr-2"
                 ></v-btn>
                 <span class="text-caption">{{ determineStatus(scan.report_status) }}</span>
            </div>
             <span v-else class="text-caption text-grey-lighten-1">No Report</span>
          </td>
          <td>
            <v-btn icon="mdi-chevron-right" variant="text" density="comfortable" color="grey"></v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-card-text>
</v-card>
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