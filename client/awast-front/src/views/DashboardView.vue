<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useScanStore } from '@/stores/scanStore';
import { storeToRefs } from 'pinia';

import DashboardChips from "../components/dashboard/DashboardChips.vue";
import DashboardPieChart from "../components/dashboard/DashboardPieChart.vue";
import DashboardLineChart from "../components/dashboard/DashboardLineChart.vue";
import ScansHistory from "../components/dashboard/ScansHistory.vue";

const authStore = useAuthStore();
const scanStore = useScanStore();
const { user } = storeToRefs(authStore);
const { scanStatus, scanHistory } = storeToRefs(scanStore);

const summaryForChips = computed(() => {
  if (!scanStatus.value?.summary) return null;
  return {
    high: scanStatus.value.summary.High || 0,
    medium: scanStatus.value.summary.Medium || 0,
    low: scanStatus.value.summary.Low || 0,
    informational: scanStatus.value.summary.Informational || 0,
  };
});

const severityForPie = computed(() => {
  if (!scanStatus.value?.summary) return { high: 0, medium: 0, low: 0 };
  return {
    high: scanStatus.value.summary.High || 0,
    medium: scanStatus.value.summary.Medium || 0,
    low: scanStatus.value.summary.Low || 0,
  };
});

const lineChartItems = computed(() => {
  if (!scanHistory.value || scanHistory.value.length === 0) return [];
  return scanHistory.value.map((scan: any) => ({
    count: 1,
    created_at: scan.created_at,
  }));
});

onMounted(async () => {
  await Promise.all([
    authStore.fetchProfile(),
    scanStore.fetchAlertsSummary(),
    scanStore.fetchScanHistory(),
  ]);
});
</script>

<template>
  <v-container fluid class="pa-6">
    <!-- Welcome / Hero Section -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="welcome-banner rounded-xl px-8 py-10 white--text">
          <h1 class="text-h4 font-weight-bold text-white mb-2">Welcome back, {{ user?.username || 'User' }} 👋</h1>
          <p class="text-subtitle-1 text-grey-lighten-4 mb-0">Here's what's happening with your security posture today.</p>
        </div>
      </v-col>
    </v-row>

    <!-- Chips zone -->
    <div class="mb-6">
      <DashboardChips :summary="summaryForChips"/>
    </div>
  <v-row class="mb-6">
    <v-col cols="12" md="4">
      <DashboardPieChart :severityCounts="severityForPie" width="100%"/>
    </v-col>
    <v-col cols="12" md="8">
      <DashboardLineChart width="100%" :items="lineChartItems"/>
    </v-col>
  </v-row>

  <v-row class="mb-6">
    <v-col cols="12">
      <ScansHistory :scans="scanHistory" />
    </v-col>
  </v-row>
  </v-container>
</template>

<style scoped>
.welcome-banner {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1), 0 4px 6px -2px rgba(79, 70, 229, 0.05);
}
</style>