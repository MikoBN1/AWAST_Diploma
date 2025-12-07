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
<!-- Chips zone -->
  <div class="pt-8 mb-16">
    <DashboardChips/>
  </div>
  <v-row class="ma-0 mb-16">
    <v-col cols="12" md="4" class="pl-0 pb-0">
      <DashboardPieChart :severityCounts="{high:12, medium: 41, low:13}" width="450"/>
    </v-col>
    <v-col cols="12" md="8" class="pb-0 pr-0">
      <DashboardLineChart width="100%" :items="items"/>
    </v-col>
  </v-row>

  <v-row class="ma-0 mb-16">
    <v-col cols="12" md="12" class="px-0 pb-0">
      <ScansHistory />
    </v-col>
  </v-row>
</template>

<style scoped>

</style>