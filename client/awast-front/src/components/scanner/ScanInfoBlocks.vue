<script setup lang="ts">
import { ref } from "vue";

const scanInfo = ref([
  {
    title: "Vulnerabilities Found",
    value: "45",
    icon: "mdi-bug",
    color: "error",
    gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  },
  {
    title: "Progress",
    value: "37",
    icon: "mdi-chart-line",
    color: "info",
    gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  },
  {
    title: "Target URL",
    value: "example.com",
    icon: "mdi-web",
    color: "success",
    gradient: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  },
  {
    title: "Start Time",
    value: "16/02/23 12:00",
    icon: "mdi-clock-outline",
    color: "warning",
    gradient: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  },
])
</script>

<template>
  <v-row>
    <v-col v-for="item in scanInfo" :key="item.title" cols="12" md="6">
        <v-card class="info-card glass-card" elevation="0">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="icon-badge" :style="{ background: item.gradient }">
                <v-icon :icon="item.icon" color="white" size="24"></v-icon>
              </div>
            </div>
            <div class="value-text mb-1">
              {{ item.title === 'Progress' ? item.value + '%' : item.value }}
            </div>
            <div class="label-text">{{ item.title }}</div>
          </v-card-text>
        </v-card>
      </v-col>
  </v-row>
  
</template>

<style scoped>
.info-card {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
  height: 100%;
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
  border-color: rgba(102, 126, 234, 0.2);
}

.icon-badge {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.value-text {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.label-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>