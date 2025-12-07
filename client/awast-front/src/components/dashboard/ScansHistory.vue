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
<v-card>
  <v-card-item>
    <v-card-title>Recent Scans</v-card-title>
  </v-card-item>
  <v-card-text>
    <v-table striped="odd" density="comfortable">
      <thead>
        <tr>
          <th v-for="(header, i) in tableHeaders" :key="i">
            {{header}}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="scan in scans" :key="scan.scan_id">
          <td>{{scan.target}}</td>
          <td>{{scan.status}}</td>
          <td>{{scan.created_at}}</td>
          <td>{{determineStatus(scan.report_status)}}</td>
          <td>View</td>
        </tr>
      </tbody>
    </v-table>
  </v-card-text>
</v-card>
</template>

<style scoped>

</style>