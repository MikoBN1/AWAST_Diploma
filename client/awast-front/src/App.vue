<script setup lang="ts">
import HeaderComponent from "./components/layout/HeaderComponent.vue";
import {computed} from "vue";
import {useRoute} from "vue-router";

const route = useRoute()
const showHeader = computed(() => !route.meta?.hideHeader)
</script>

<template>
  <div>
    <HeaderComponent v-if="showHeader"/>
  </div>
  <div class="container-fluid">
    <RouterView />
  </div>
</template>

<style scoped>
.container-fluid{
  max-width: 96vw;
  margin: 0 auto;
}

@media screen and (min-width: 1920px){
  .container-fluid{
    max-width: 1400px;
  }
}

@media screen and (max-width: 600px) {
  .container-fluid{
    max-width: 100vw;
  }
}
</style>
