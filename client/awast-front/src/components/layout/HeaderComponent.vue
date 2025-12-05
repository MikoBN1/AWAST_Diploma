<script setup lang="ts">
import logo from '../../assets/img/logo.svg'
</script>

<template>
  <div class="header-wrapper">
    <header class="header">
      <v-row>
        <v-col class="d-flex align-center py-0">
          <v-img  :src=logo
                  alt="Login Image"
                  max-width="200"
                  class="logo"
          />
        </v-col>
        <v-col>

        </v-col>
        <v-col>
          <v-row class="ga-5 pr-0 ma-0" justify="end">
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
              <i class="bi bi-gear resize-icon"></i>
            </div><div>
            <i class="bi bi-box-arrow-right resize-icon mr-5"></i>
          </div>
          </v-row>

        </v-col>
      </v-row>
    </header>
  </div>
</template>

<style scoped>
.header {
  background-color: var(--layout);
  height: 70px;
  left: 0;
  margin-right: 0;
  position: fixed;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  z-index: 1000;
  border-bottom: #ebebeb solid 1px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.header-wrapper{
  display: flex;
  justify-content: end;
  height: 70px;
}
.resize-icon {
  font-size: 32px;
}
.bi{
  color: var(--text-color);
}
</style>