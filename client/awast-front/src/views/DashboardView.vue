<script setup lang="ts">

import DashboardChips from "../components/dashboard/DashboardChips.vue";
import DashboardPieChart from "../components/dashboard/DashboardPieChart.vue";
</script>

<template>
<!-- Chips zone -->
  <div class="pt-8 pb-16">
    <DashboardChips/>
  </div>
  <v-row class="ma-0">
    <v-col cols="12" md="4" class="pl-0">
      <DashboardPieChart :severityCounts="{high:12, medium: 41, low:13}" width="450"/>
    </v-col>
  </v-row>
</template>

<style scoped>

</style>