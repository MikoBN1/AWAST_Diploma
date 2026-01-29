<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dialog = ref(props.modelValue)

// Sync dialog state with props
import { watch } from 'vue'
watch(() => props.modelValue, (val) => {
  dialog.value = val
})
watch(dialog, (val) => {
  emit('update:modelValue', val)
})

const isDarkTheme = ref(false)
const selectedLanguage = ref('en')

const languages = [
  { title: 'English', value: 'en' },
  { title: 'Русский', value: 'ru' }
]
</script>

<template>
  <v-dialog
    v-model="dialog"
    max-width="500px"
  >
    <v-card class="rounded-lg">
      <v-card-title class="d-flex justify-space-between align-center pa-4">
        <span class="text-h6 font-weight-bold">Settings</span>
        <v-btn
          icon="bi-x"
          variant="text"
          density="comfortable"
          @click="dialog = false"
        >
          <i class="bi bi-x" style="font-size: 1.5rem;"></i>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <!-- Theme Section -->
        <div class="mb-6">
          <div class="text-subtitle-1 mb-2 font-weight-medium">Appearance</div>
          <v-list-item class="px-0">
            <template v-slot:prepend>
              <div class="d-flex align-center mr-4">
                <i :class="isDarkTheme ? 'bi bi-moon-stars' : 'bi bi-sun'" class="text-h6"></i>
              </div>
            </template>
            <v-list-item-title>Dark Mode</v-list-item-title>
            <template v-slot:append>
              <v-switch
                v-model="isDarkTheme"
                color="primary"
                hide-details
                inset
              ></v-switch>
            </template>
          </v-list-item>
        </div>

        <!-- Language Section -->
        <div>
          <div class="text-subtitle-1 mb-2 font-weight-medium">Language</div>
          <v-select
            v-model="selectedLanguage"
            :items="languages"
            item-title="title"
            item-value="value"
            variant="outlined"
            density="comfortable"
            hide-details
            prepend-inner-icon="bi-translate"
          ></v-select>
        </div>
      </v-card-text>

      <v-card-actions class="pa-4 pt-0 justify-end">
        <v-btn
          variant="text"
          @click="dialog = false"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.v-card-title {
  background-color: var(--surface);
}
</style>
