<script setup lang="ts">

</script>

<template>
<v-row>
  <v-col>
    <v-card elevation="1" rounded>
      <v-card-item>
        <v-card-title>
          <div class="icon-wrapper">
            <i class="bi bi-activity"></i>
          </div>
        </v-card-title>
      </v-card-item>
      <v-card-text>
        <p class="sub-text mb-2">Total Scans</p>
        <p class="value">1,247</p>
      </v-card-text>
    </v-card>
  </v-col>
  <v-col>
    <v-card elevation="1" rounded>
      <v-card-item>
        <v-card-title>
          <div class="icon-wrapper red-colored">
            <i class="bi bi-exclamation-triangle"></i>
          </div>
        </v-card-title>
      </v-card-item>
      <v-card-text>
        <p class="sub-text mb-2">High</p>
        <p class="value">47</p>
      </v-card-text>
    </v-card>
  </v-col>
  <v-col>
    <v-card elevation="1" rounded>
      <v-card-item>
        <v-card-title>
          <div class="icon-wrapper orange-colored">
            <i class="bi bi-exclamation-triangle"></i>
          </div>
        </v-card-title>
      </v-card-item>
      <v-card-text>
        <p class="sub-text mb-2">Medium</p>
        <p class="value">1,247</p>
      </v-card-text>
    </v-card>
  </v-col>
  <v-col>
    <v-card elevation="1" rounded>
      <v-card-item>
        <v-card-title>
          <div class="icon-wrapper green-colored">
            <i class="bi bi-exclamation-triangle"></i>
          </div>
        </v-card-title>
      </v-card-item>
      <v-card-text>
        <p class="sub-text mb-2">Low</p>
        <p class="value">1,247</p>
      </v-card-text>
    </v-card>
  </v-col>

</v-row>
</template>

<style scoped>
.icon-wrapper {
  width: 32px;
  height: 32px;
  background-color: #1F51FF;
  color: #fff;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  font-size: 20px;
}

.orange-colored{
  background: var(--medium-severity);
}
.red-colored{
  background: var(--critical-severity);
}
.green-colored{
  background: var(--low-severity);
}
.sub-text {
  color: var(--sub-text);
}
.value{
  color: var(--text-color);
}
</style>