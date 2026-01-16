<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore';
import { storeToRefs } from 'pinia';
import { onMounted } from 'vue';

const authStore = useAuthStore();
const {user} = storeToRefs(authStore);

onMounted(() => {
    authStore.fetchProfile();
});

</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card v-if="user" class="pa-4">
          <v-card-title class="text-h4 mb-4">
            User Profile
          </v-card-title>
          
          <v-card-text>
            <v-list>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-account" class="mr-4"></v-icon>
                </template>
                <v-list-item-title>Username</v-list-item-title>
                <v-list-item-subtitle class="text-body-1 mt-1">
                  {{ user.username }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-divider class="my-2"></v-divider>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-email" class="mr-4"></v-icon>
                </template>
                <v-list-item-title>Email</v-list-item-title>
                <v-list-item-subtitle class="text-body-1 mt-1">
                  {{ user.email }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-divider class="my-2"></v-divider>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-domain" class="mr-4"></v-icon>
                </template>
                <v-list-item-title>Enabled Domains</v-list-item-title>
                <v-list-item-subtitle class="text-body-1 mt-1">
                  <v-chip-group v-if="user.enabled_domains && user.enabled_domains.length > 0">
                    <v-chip
                      v-for="domain in user.enabled_domains"
                      :key="domain"
                      color="primary"
                      variant="tonal"
                    >
                      {{ domain }}
                    </v-chip>
                  </v-chip-group>
                  <span v-else class="text-caption text-medium-emphasis">
                    No domains enabled
                  </span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
        
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
