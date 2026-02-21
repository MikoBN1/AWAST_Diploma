<script setup lang="ts">
interface SummaryData {
  high: number;
  medium: number;
  low: number;
  informational: number;
}

const props = withDefaults(defineProps<{
  summary?: SummaryData | null;
}>(), {
  summary: null,
});

const totalVulnerabilities = computed(() => {
  if (!props.summary) return 0;
  return props.summary.high + props.summary.medium + props.summary.low + props.summary.informational;
});

import { computed } from 'vue';
</script>

<template>
<v-row>
  <v-col cols="12" sm="6" lg="3">
    <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Total Vulnerabilities</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">{{ totalVulnerabilities }}</h3>
        </div>
        <div class="icon-box bg-blue-lighten-5 text-blue-darken-2">
           <v-icon icon="mdi-shield-bug-outline" size="24"></v-icon>
        </div>
      </div>
    </v-card>
  </v-col>

  <v-col cols="12" sm="6" lg="3">
     <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">High Severity</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">{{ summary?.high ?? 0 }}</h3>
        </div>
        <div class="icon-box bg-red-lighten-5 text-red-darken-2">
           <v-icon icon="mdi-alert-octagon-outline" size="24"></v-icon>
        </div>
      </div>
    </v-card>
  </v-col>

  <v-col cols="12" sm="6" lg="3">
      <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Medium Severity</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">{{ summary?.medium ?? 0 }}</h3>
        </div>
        <div class="icon-box bg-amber-lighten-5 text-amber-darken-3">
           <v-icon icon="mdi-alert-outline" size="24"></v-icon>
        </div>
      </div>
    </v-card>
  </v-col>
  
  <v-col cols="12" sm="6" lg="3">
    <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Low Severity</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">{{ summary?.low ?? 0 }}</h3>
        </div>
        <div class="icon-box bg-green-lighten-5 text-green-darken-2">
           <v-icon icon="mdi-check-circle-outline" size="24"></v-icon>
        </div>
      </div>
    </v-card>
  </v-col>

</v-row>
</template>

<style scoped>
.stats-card {
  border: 1px solid rgba(0,0,0,0.05);
  background: white;
  transition: all 0.3s ease;
}
.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
}
.icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>