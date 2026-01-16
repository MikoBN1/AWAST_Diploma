<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore';
import { storeToRefs } from 'pinia';
import { onMounted } from 'vue';

import { useScanStore } from '@/stores/scanStore';

const authStore = useAuthStore();
const scanStore = useScanStore();
const { user } = storeToRefs(authStore);
const { scanStatus } = storeToRefs(scanStore);

onMounted(() => {
    authStore.fetchProfile();
    scanStore.fetchAlertsSummary();
});

</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <template v-if="user">
        <v-card class="pa-0" elevation="2" rounded="lg">
          <v-sheet color="primary" height="120" class="position-relative">
             <div class="d-flex justify-center align-center h-100">
             </div>
             <v-avatar
                color="surface"
                size="100"
                class="position-absolute"
                style="bottom: -50px; left: 50%; transform: translateX(-50%); border: 4px solid rgb(var(--v-theme-surface));"
             >
                <v-icon icon="mdi-account" size="60" color="primary"></v-icon>
             </v-avatar>
          </v-sheet>

          <v-card-text class="pt-16 mt-4 text-center">
            <h2 class="text-h4 font-weight-bold">{{ user.username }}</h2>
            <div class="text-body-1 text-medium-emphasis mb-4">{{ user.email }}</div>
            
            <v-divider class="my-4"></v-divider>

            <div class="text-left">
              <div class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon icon="mdi-domain" size="small" class="mr-2" color="primary"></v-icon>
                Enabled Domains
              </div>
              <v-chip-group v-if="user.enabled_domains?.length">
                <v-chip
                  v-for="domain in user.enabled_domains"
                  :key="domain"
                  color="primary"
                  variant="outlined"
                  size="small"
                >
                  {{ domain }}
                </v-chip>
              </v-chip-group>
              <div v-else class="text-caption text-medium-emphasis">
                No domains enabled
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-row class="mt-4">
          <v-col cols="12" sm="6">
            <v-card class="pa-4 h-100 d-flex flex-column align-center justify-center" elevation="2" rounded="lg">
              <v-icon icon="mdi-shield-check-outline" size="48" color="primary" class="mb-2"></v-icon>
              <div class="text-caption text-uppercase text-medium-emphasis font-weight-bold">Monitored Domains</div>
              <div class="text-h3 font-weight-bold text-primary">
                {{ user?.enabled_domains?.length || 0 }}
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6">
            <v-card class="pa-4 h-100 d-flex flex-column align-center justify-center" elevation="2" rounded="lg">
              <v-icon icon="mdi-alert-circle-outline" size="48" color="error" class="mb-2"></v-icon>
              <div class="text-caption text-uppercase text-medium-emphasis font-weight-bold">Total Vulnerabilities</div>
              <div class="text-h3 font-weight-bold text-error">
                 {{ scanStatus?.summary ? (scanStatus.summary.High + scanStatus.summary.Medium + scanStatus.summary.Low + scanStatus.summary.Informational) : 0 }}
              </div>
            </v-card>
          </v-col>
          
           <v-col cols="12">
            <v-card class="pa-4" elevation="2" rounded="lg">
              <v-card-title class="text-subtitle-1 font-weight-bold mb-4">
                 <v-icon icon="mdi-chart-bar" class="mr-2" color="secondary"></v-icon>
                 Vulnerability Distribution
              </v-card-title>
              <v-card-text>
                <v-row v-if="scanStatus?.summary" no-gutters>
                  <v-col cols="6" sm="3" class="d-flex flex-column align-center px-2 py-4 border-e-sm">
                    <div class="text-h4 font-weight-bold text-red">{{ scanStatus.summary.High || 0 }}</div>
                    <div class="text-caption text-uppercase font-weight-bold mt-1">High</div>
                  </v-col>
                  <v-col cols="6" sm="3" class="d-flex flex-column align-center px-2 py-4 border-e-sm-md-and-up">
                    <div class="text-h4 font-weight-bold text-orange">{{ scanStatus.summary.Medium || 0 }}</div>
                    <div class="text-caption text-uppercase font-weight-bold mt-1">Medium</div>
                  </v-col>
                  <v-col cols="6" sm="3" class="d-flex flex-column align-center px-2 py-4 border-e-sm">
                    <div class="text-h4 font-weight-bold text-yellow-darken-2">{{ scanStatus.summary.Low || 0 }}</div>
                    <div class="text-caption text-uppercase font-weight-bold mt-1">Low</div>
                  </v-col>
                  <v-col cols="6" sm="3" class="d-flex flex-column align-center px-2 py-4">
                    <div class="text-h4 font-weight-bold text-info">{{ scanStatus.summary.Informational || 0 }}</div>
                    <div class="text-caption text-uppercase font-weight-bold mt-1">Info</div>
                  </v-col>
                </v-row>
                <div v-else class="text-center py-8 text-medium-emphasis">
                  <v-icon icon="mdi-chart-bar-off" size="large" class="mb-2"></v-icon>
                  <div>No scan data available</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        </template>
        
        <v-alert
          v-else
          type="warning"
          title="Profile Not Found"
          text="Unable to load user profile information."
        ></v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
</style>
