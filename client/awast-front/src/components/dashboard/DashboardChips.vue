<script setup lang="ts">

</script>

<template>
<v-row>
  <v-col cols="12" sm="6" lg="3">
    <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Total Vulnerabilities</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">1,247</h3>
        </div>
        <div class="icon-box bg-blue-lighten-5 text-blue-darken-2">
           <v-icon icon="mdi-shield-bug-outline" size="24"></v-icon>
        </div>
      </div>
      <div class="d-flex align-center mt-2">
        <v-chip size="x-small" color="success" class="font-weight-bold" variant="flat">
          <v-icon start icon="mdi-arrow-up" size="12"></v-icon> 12%
        </v-chip>
        <span class="text-caption text-grey ml-2">vs last week</span>
      </div>
    </v-card>
  </v-col>

  <v-col cols="12" sm="6" lg="3">
     <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Critical Issues</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">47</h3>
        </div>
        <div class="icon-box bg-red-lighten-5 text-red-darken-2">
           <v-icon icon="mdi-alert-octagon-outline" size="24"></v-icon>
        </div>
      </div>
      <div class="d-flex align-center mt-2">
        <v-chip size="x-small" color="error" class="font-weight-bold" variant="flat">
          <v-icon start icon="mdi-arrow-up" size="12"></v-icon> 5%
        </v-chip>
        <span class="text-caption text-grey ml-2">vs last week</span>
      </div>
    </v-card>
  </v-col>

  <v-col cols="12" sm="6" lg="3">
      <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Medium Issues</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">247</h3>
        </div>
        <div class="icon-box bg-amber-lighten-5 text-amber-darken-3">
           <v-icon icon="mdi-alert-outline" size="24"></v-icon>
        </div>
      </div>
      <div class="d-flex align-center mt-2">
        <v-chip size="x-small" color="success" class="font-weight-bold" variant="flat">
          <v-icon start icon="mdi-arrow-down" size="12"></v-icon> 2%
        </v-chip>
        <span class="text-caption text-grey ml-2">vs last week</span>
      </div>
    </v-card>
  </v-col>
  
  <v-col cols="12" sm="6" lg="3">
    <v-card class="stats-card pa-4" elevation="0">
      <div class="d-flex justify-space-between align-start mb-2">
        <div>
          <span class="text-subtitle-2 text-grey-darken-1 font-weight-medium">Safe Services</span>
          <h3 class="text-h4 font-weight-bold text-slate-800 mt-1">1,022</h3>
        </div>
        <div class="icon-box bg-green-lighten-5 text-green-darken-2">
           <v-icon icon="mdi-check-circle-outline" size="24"></v-icon>
        </div>
      </div>
      <div class="d-flex align-center mt-2">
        <v-chip size="x-small" color="success" class="font-weight-bold" variant="flat">
          <v-icon start icon="mdi-arrow-up" size="12"></v-icon> 8%
        </v-chip>
        <span class="text-caption text-grey ml-2">vs last week</span>
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