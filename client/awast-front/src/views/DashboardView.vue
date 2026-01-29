<script setup lang="ts">

import DashboardChips from "../components/dashboard/DashboardChips.vue";
import DashboardPieChart from "../components/dashboard/DashboardPieChart.vue";
import DashboardLineChart from "../components/dashboard/DashboardLineChart.vue";
import ScansHistory from "../components/dashboard/ScansHistory.vue";

const items = [
  { count: 4, created_at: "2025-01-01T12:00:00Z" },
  { count: 7, created_at: "2025-01-02T12:00:00Z" },
  { count: 3, created_at: "2025-01-03T12:00:00Z" },
  { count: 10, created_at: "2025-01-04T12:00:00Z" }
]
</script>

<template>
  <v-container fluid class="pa-6">
    <!-- Welcome / Hero Section -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="welcome-banner rounded-xl px-8 py-10 white--text">
          <h1 class="text-h4 font-weight-bold text-white mb-2">Welcome back, Admin 👋</h1>
          <p class="text-subtitle-1 text-grey-lighten-4 mb-0">Here's what's happening with your security posture today.</p>
        </div>
      </v-col>
    </v-row>

    <!-- Chips zone -->
    <div class="mb-6">
      <DashboardChips/>
    </div>
  <v-row class="mb-6">
    <v-col cols="12" md="4">
      <DashboardPieChart :severityCounts="{high:12, medium: 41, low:13}" width="100%"/>
    </v-col>
    <v-col cols="12" md="8">
      <DashboardLineChart width="100%" :items="items"/>
    </v-col>
  </v-row>

  <v-row class="mb-6">
    <v-col cols="12">
      <ScansHistory />
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