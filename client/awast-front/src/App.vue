<script setup lang="ts">
import HeaderComponent from "./components/layout/HeaderComponent.vue";
import NavigationSidebar from "./components/layout/NavigationSidebar.vue";
import {computed} from "vue";
import {useRoute} from "vue-router";

const route = useRoute()
const showHeader = computed(() => !route.meta?.hideHeader)
</script>

<template>
  <v-app>
    <NavigationSidebar v-if="showHeader" />
    <HeaderComponent v-if="showHeader" />
    <v-main>
      <div class="container-fluid">
        <RouterView />
      </div>
    </v-main>
  </v-app>
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
