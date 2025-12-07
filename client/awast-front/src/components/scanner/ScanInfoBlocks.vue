<script setup lang="ts">
import {ref} from "vue";

const scanInfo = ref([
  {
    title: "Vulnerabilities Found",
    value: "45",
  },
  {
    title: "Progress",
    value: "37",
  },
  {
    title: "Target URL",
    value: "example.com",
  },
  {
    title: "Start Time",
    value: "16/02/23 12:00",
  },
])
</script>

<template>
  <v-card v-for="item in scanInfo" :key="item.title" width="180">
    <v-card-text class="card-text">
      <div class="card-content">
        <h2>{{item.title==='Progress'?item.value + '%' : item.value}}</h2>
        <p class="sub-text">
          {{item.title}}
        </p>
      </div>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.sub-text{
  color: var(--sub-text);
}
h2{
  text-align: center;
  overflow-wrap: anywhere;
}
.card-content{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.v-card-text {
  height: 100%;
  display: flex;
  justify-content: center;
}
</style>