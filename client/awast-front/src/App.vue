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
  <RouterView />
</template>

<style scoped>
.left-content {
  display: flex;
  gap: 32px;
}
.sidebar{
  margin-right: 32px;
}
.card{
  background-color: var(--bg-color);
}
.main{
  margin-top: 70px;
  min-height: calc(100vh - 70px);
  padding-bottom: 24px;
}
.container-fluid{
  max-width: calc(88vw - 250px);
  margin: 0 auto;
}

@media screen and (min-width: 1920px){
  .container-fluid{
    max-width: 1400px;
  }
}

@media screen and (max-width: 1080px){
  .container-fluid{
    max-width: 90vw;
  }
  .sidebar{
    margin: 0;
    display: none;
  }
  .main{
    padding-left: 0 !important;
  }
}

@media screen and (max-width: 600px) {
  .container-fluid{
    max-width: 100vw;
  }
}
</style>
