<script setup lang="ts">
import SettingsDialog from '../dialogs/SettingsDialog.vue'
import { ref } from 'vue'
import { useLayoutStore } from '../../stores/layoutStore';

const isSettingsDialogOpen = ref(false)
const layoutStore = useLayoutStore();
</script>

<template>
  <v-app-bar app elevation="1" color="white" height="70">
    <template v-slot:prepend>
      <v-app-bar-nav-icon 
        variant="text" 
        color="grey-darken-1" 
        @click="layoutStore.toggleRail()"
      ></v-app-bar-nav-icon>
    </template>

    <v-spacer></v-spacer>

    <template v-slot:append>
       <div class="d-flex align-center ga-5 pr-2">
            <!--    User Account    -->
            <div>
              <router-link to="/profile">
                <i
                    class="bi bi-person-circle resize-icon"
                    style="cursor: pointer;"
                />
              </router-link>
            </div>
            <!--    Account Settings   -->
            <div>
              <i
                class="bi bi-gear resize-icon"
                style="cursor: pointer;"
                @click="isSettingsDialogOpen = true"
              ></i>
            </div>
            <div>  
              <router-link to="/auth/login">
                <i class="bi bi-box-arrow-right resize-icon mr-5"></i>
              </router-link>
            </div>
       </div>
    </template>

    <SettingsDialog v-model="isSettingsDialogOpen" />
  </v-app-bar>
</template>

<style scoped>
.resize-icon {
  font-size: 24px;
}
.bi{
  color: var(--text-color);
  transition: color 0.2s;
}
</style>