<script setup lang="ts">
  import {ref} from "vue";

  const vulns = ref([
    {
      severity: "high",
      value: "23",
      color: "red"
    },
    {
      severity: "medium",
      value: "10",
      color: "orange"
    },
    {
      severity: "low",
      value: "2",
      color: "green"
    },
  ])
</script>

<template>
<v-card>
  <v-card-title>
    <h4>Vulnerabilities Summary</h4>
    <p class="sub-text mb-3">Count of how much vulns and what severity was found</p>
  </v-card-title>
  <v-card-text>
    <div v-for="item in vulns" :key="item.severity" class="mb-6">
      <div class="d-flex justify-space-between mb-2">
        <div>
          <v-avatar size="10" :color="item.color" class="mr-3"></v-avatar>
          <span class="text-capitalize">{{ item.severity }}</span>
        </div>
        <span>{{ item.value }}</span>
      </div>
      <v-progress-linear :height="6" rounded :model-value="item.value" max="45"></v-progress-linear>
    </div>
    <v-divider></v-divider>
    <div class="d-flex justify-space-between pt-4 mb-4">
      <p class="sub-text">Total Vulnerabilities Found</p>
      <p>45</p>
    </div>
    <div class="d-flex justify-space-between ga-4">
        <v-col class="d-flex justify-center flex-column align-center rounded-lg" style="background-color: #e3e3e3">
          <h2>{{'23'}}</h2>
          <p class="sub-text">High Vulnerabilities</p>
        </v-col>
        <v-col class="d-flex justify-center flex-column align-center rounded-lg" style="background-color: #e3e3e3">
          <h2>{{'Full'}}</h2>
          <p class="sub-text">Scan Type</p>
        </v-col>
    </div>
  </v-card-text>
</v-card>
</template>

<style scoped>
.sub-text{
  color: var(--sub-text);
}
p{
  font-size: 16px;
}
</style>