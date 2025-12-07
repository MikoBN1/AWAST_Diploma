<script setup lang="ts">
import {ref} from "vue";
import ScanInfoBlocks from "../components/scanner/ScanInfoBlocks.vue";
import ScanVulnerabilitiesProgress from "../components/scanner/ScanVulnerabilitiesProgress.vue";
const model = ref(true)
const visible = ref(false)
</script>

<template>
  <v-row justify="center" class="py-8">
    <h1>Vulnerability Scanner</h1>
  </v-row>

  <v-row justify="center" class="mb-8">
    <v-card min-width="400">
      <v-card-item>
        <v-card-title>
          <div class="title-wrapper pt-4">
            <div class="web-icon-wrapper mb-4">
              <span class="mdi mdi-web"></span>
            </div>
            <p class="title-text mb-1">Scan Web Application</p>
            <p class="sub-text">Connect your Git repository for <br/> comprehensive codebase analysis</p>
          </div>
        </v-card-title>
        <v-card-text>
          <v-label>URL</v-label>
          <v-text-field
              density="compact"
              placeholder="example.com"
              prepend-inner-icon="mdi-search-web"
              variant="outlined"
          ></v-text-field>
        <!--     User creds     -->
          <v-switch
              v-model="model"
              label="User credentials"
              append-icon="mdi-information-outline"
              hide-details
              color="primary"
          ></v-switch>
          <v-label>Login</v-label>
          <v-text-field
              density="compact"
              placeholder="username or email"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              :disabled="!model"
          ></v-text-field>
          <v-label>Password</v-label>
          <v-text-field
              :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
              :type="visible ? 'text' : 'password'"
              density="compact"
              placeholder="Enter your password"
              prepend-inner-icon="mdi-lock-outline"
              variant="outlined"
              @click:append-inner="visible = !visible"
              :disabled="!model"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="flat" color="var(--button-bg)" theme="dark" class="start-btn">
            Start Scan
          </v-btn>
        </v-card-actions>
      </v-card-item>
    </v-card>
  </v-row>

  <v-row justify="center" class="mb-8 ga-4">
    <ScanInfoBlocks/>
  </v-row>

  <v-row justify="center" class="mb-8">
    <ScanVulnerabilitiesProgress/>
  </v-row>
</template>

<style scoped>
.start-btn{
  width: 100%;
}
.web-icon-wrapper{
  width: 60px;
  height: 60px;
  background-color: #e3e3e3;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 32px;
  border-radius: 100%;
}
.title-wrapper{
  display: flex;
  align-items: center;
  flex-direction: column;
  margin-bottom: 16px;
}
.title-text{
  color: var(--text-color);
  font-weight: 400;
  font-size: 14px;

}
.sub-text{
  color: var(--sub-text);
  text-align: center;
  font-size: 14px
}
</style>