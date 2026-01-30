<script setup lang="ts">
import { useLayoutStore } from '../../stores/layoutStore';
import logo from '../../assets/img/mini-logo.svg';
import logo2 from '../../assets/img/logo.svg';

const layoutStore = useLayoutStore();
</script>

<template>
  <v-navigation-drawer
    v-model="layoutStore.drawer"
    :rail="layoutStore.rail"
    permanent
    app
    @click="layoutStore.rail = false"
    color="white"
    class="sidebar-drawer"
    elevation="2"
  >
    <v-list-item
      class="px-2 py-4 brand-area"
    >
        <div class="d-flex align-center">
            <img v-if="layoutStore.rail" :src="logo" alt="AWAST" class="logo-img" width="40" height="40" />
            <img v-else :src="logo2" alt="AWAST" class="logo-img" width="auto" height="40" />
        </div>
    </v-list-item>

    <v-divider></v-divider>

    <v-list density="compact" nav class="mt-4">
      <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" value="dashboard" to="/dashboard" active-color="primary" rounded="lg"></v-list-item>
      <v-list-item prepend-icon="mdi-shield-search" title="Scanner" value="scanner" to="/scanner" active-color="primary" rounded="lg"></v-list-item>
      <v-list-item prepend-icon="mdi-history" title="Scan History" value="history" to="/scanner/history" active-color="primary" rounded="lg"></v-list-item>
      <v-list-item prepend-icon="mdi-api" title="Swagger AI" value="swagger" to="/swagger-analysis" active-color="primary" rounded="lg"></v-list-item>
      
      <v-list-subheader v-if="!layoutStore.rail" class="text-caption text-uppercase font-weight-bold text-grey">Administration</v-list-subheader>
       <v-list-item prepend-icon="mdi-account-group" title="User Management" value="users" to="/admin/users" active-color="primary" rounded="lg"></v-list-item>

    </v-list>
    
    <template v-slot:append>
       <v-list density="compact" nav>
         <v-list-item prepend-icon="mdi-account-circle" title="Profile" value="profile" to="/profile" active-color="primary" rounded="lg"></v-list-item>
       </v-list>
    </template>
  </v-navigation-drawer>
</template>

<style scoped>
.sidebar-drawer {
    border-right: 1px solid rgba(0,0,0,0.05) !important;
}
.brand-area {
    height: 70px; /* Match header height roughly */
    display: flex;
    align-items: center;
}
.logo-img {
    object-fit: contain;
}
</style>
