<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { ApiScanConfig } from '../../types/apiScanner'

const emit = defineEmits<{
  (e: 'scan', config: ApiScanConfig): void
}>()

const form = ref()
const fileInput = ref<HTMLInputElement | null>(null)
const file = ref<File | undefined>(undefined)
const fileError = ref('')
const showToken = ref(false)
const showSecondaryToken = ref(false)

const cfg = reactive({
  token_value: '',
  base_url: '',
  secondary_token_value: '',
  secondary_token_type: 'Bearer',
  secondary_token_location: 'header' as 'header' | 'cookie' | 'query',
  secondary_token_name: 'Authorization',
  cookie_name: '',
  cookie_value: '',
  api_key_name: '',
  api_key_value: '',
  api_key_location: 'header' as 'header' | 'query',
  max_concurrency: 5,
  request_delay_ms: 0,
  time_analysis: false,
  enumerate_mode: false,
  ratelimit_mode: false,
  ratelimit_burst_count: 10,
  cors_mode: false,
  header_check_mode: false,
  custom_wordlist: '',
})

const tokenRules = [(v: string) => !!v || 'Primary token is required']

const validExtensions = ['.json', '.yaml', '.yml']
const validateFile = (f: File) => validExtensions.includes(f.name.substring(f.name.lastIndexOf('.')).toLowerCase())

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) {
    file.value = target.files[0]
    fileError.value = ''
  }
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer?.files?.[0]) {
    file.value = event.dataTransfer.files[0]
    fileError.value = ''
  }
}

const submit = async () => {
  if (!file.value) {
    fileError.value = 'Please upload an OpenAPI spec file'
    return
  }
  if (!validateFile(file.value)) {
    fileError.value = 'Only .json, .yaml, .yml files are accepted'
    return
  }
  const { valid } = await form.value.validate()
  if (!valid) return

  const config: ApiScanConfig = {
    spec_file: file.value,
    token_value: cfg.token_value,
  }

  if (cfg.base_url) config.base_url = cfg.base_url
  if (cfg.secondary_token_value) {
    config.secondary_token_value = cfg.secondary_token_value
    config.secondary_token_type = cfg.secondary_token_type
    config.secondary_token_location = cfg.secondary_token_location
    config.secondary_token_name = cfg.secondary_token_name
  }
  if (cfg.cookie_name && cfg.cookie_value) {
    config.cookie_name = cfg.cookie_name
    config.cookie_value = cfg.cookie_value
  }
  if (cfg.api_key_name && cfg.api_key_value) {
    config.api_key_name = cfg.api_key_name
    config.api_key_value = cfg.api_key_value
    config.api_key_location = cfg.api_key_location
  }
  config.max_concurrency = cfg.max_concurrency
  config.request_delay_ms = cfg.request_delay_ms
  if (cfg.time_analysis) config.time_analysis = true
  if (cfg.enumerate_mode) config.enumerate_mode = true
  if (cfg.ratelimit_mode) {
    config.ratelimit_mode = true
    config.ratelimit_burst_count = cfg.ratelimit_burst_count
  }
  if (cfg.cors_mode) config.cors_mode = true
  if (cfg.header_check_mode) config.header_check_mode = true
  if (cfg.custom_wordlist) config.custom_wordlist = cfg.custom_wordlist

  emit('scan', config)
}
</script>

<template>
  <v-form ref="form" @submit.prevent="submit">
    <!-- Spec File Upload -->
    <v-card class="form-card mb-4" elevation="0">
      <v-card-text class="pa-6">
        <div class="section-label mb-4">
          <v-icon icon="mdi-file-code" color="primary" class="mr-2"></v-icon>
          <span class="text-subtitle-1 font-weight-bold text-slate-800">OpenAPI Specification</span>
          <v-chip size="x-small" color="error" variant="flat" class="ml-2">Required</v-chip>
        </div>

        <div
          class="drop-zone"
          :class="{ 'drop-zone--error': !!fileError }"
          @dragover.prevent
          @drop="onDrop"
          @click="fileInput?.click()"
        >
          <input
            ref="fileInput"
            type="file"
            class="d-none"
            accept=".json,.yaml,.yml"
            @change="handleFileChange"
          >

          <div v-if="!file" class="text-center py-6">
            <div class="icon-wrapper mb-3">
              <v-icon icon="mdi-cloud-upload-outline" size="36" color="primary"></v-icon>
            </div>
            <p class="text-body-2 font-weight-medium text-slate-700 mb-1">Drop your spec here or click to browse</p>
            <div class="mt-3">
              <v-chip size="small" color="primary" variant="outlined" class="mr-1">.json</v-chip>
              <v-chip size="small" color="primary" variant="outlined" class="mr-1">.yaml</v-chip>
              <v-chip size="small" color="primary" variant="outlined">.yml</v-chip>
            </div>
          </div>

          <div v-else class="d-flex align-center pa-2">
            <v-icon icon="mdi-file-check" size="36" color="primary" class="mr-3"></v-icon>
            <div class="flex-grow-1">
              <div class="text-body-1 font-weight-medium text-slate-800">{{ file.name }}</div>
              <div class="text-caption text-grey-darken-1">{{ (file.size / 1024).toFixed(1) }} KB</div>
            </div>
            <v-btn icon="mdi-close" variant="text" color="grey" size="small" @click.stop="file = undefined"></v-btn>
          </div>
        </div>

        <v-alert v-if="fileError" type="error" variant="tonal" density="compact" class="mt-3">
          {{ fileError }}
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Primary Token + Base URL -->
    <v-card class="form-card mb-4" elevation="0">
      <v-card-text class="pa-6">
        <div class="section-label mb-4">
          <v-icon icon="mdi-shield-key" color="primary" class="mr-2"></v-icon>
          <span class="text-subtitle-1 font-weight-bold text-slate-800">Authentication & Target</span>
        </div>

        <v-text-field
          v-model="cfg.token_value"
          label="Primary Bearer Token"
          placeholder="Bearer eyJhbGci..."
          :type="showToken ? 'text' : 'password'"
          :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showToken = !showToken"
          :rules="tokenRules"
          variant="outlined"
          density="comfortable"
          class="mb-3"
          required
        >
          <template #prepend-inner>
            <v-icon icon="mdi-key" color="grey" size="18"></v-icon>
          </template>
        </v-text-field>

        <v-text-field
          v-model="cfg.base_url"
          label="Target Base URL"
          placeholder="https://api.example.com"
          variant="outlined"
          density="comfortable"
          hint="Required for live checks. Leave empty for static analysis only."
          persistent-hint
        >
          <template #prepend-inner>
            <v-icon icon="mdi-web" color="grey" size="18"></v-icon>
          </template>
        </v-text-field>
      </v-card-text>
    </v-card>

    <!-- Advanced Auth -->
    <v-expansion-panels variant="accordion" class="mb-4">
      <v-expansion-panel rounded="xl" elevation="0" class="form-card">
        <v-expansion-panel-title class="pa-6">
          <div class="d-flex align-center">
            <v-icon icon="mdi-lock-plus-outline" color="primary" class="mr-2"></v-icon>
            <span class="text-subtitle-1 font-weight-bold text-slate-800">Additional Auth</span>
            <v-chip size="x-small" variant="tonal" color="primary" class="ml-2">Optional</v-chip>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text class="px-6 pb-6">

          <!-- Secondary token -->
          <p class="text-caption font-weight-bold text-uppercase text-grey-darken-1 mb-3">Secondary Token (BOLA / BFLA checks)</p>
          <v-text-field
            v-model="cfg.secondary_token_value"
            label="Secondary Token"
            placeholder="Bearer eyJ..."
            :type="showSecondaryToken ? 'text' : 'password'"
            :append-inner-icon="showSecondaryToken ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="showSecondaryToken = !showSecondaryToken"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-text-field>

          <v-row dense class="mb-4">
            <v-col cols="4">
              <v-text-field v-model="cfg.secondary_token_type" label="Type" placeholder="Bearer" variant="outlined" density="compact"></v-text-field>
            </v-col>
            <v-col cols="4">
              <v-select
                v-model="cfg.secondary_token_location"
                label="Location"
                :items="['header', 'cookie', 'query']"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>
            <v-col cols="4">
              <v-text-field v-model="cfg.secondary_token_name" label="Key Name" variant="outlined" density="compact"></v-text-field>
            </v-col>
          </v-row>

          <!-- Cookie Auth -->
          <v-divider class="mb-4"></v-divider>
          <p class="text-caption font-weight-bold text-uppercase text-grey-darken-1 mb-3">Cookie Auth</p>
          <v-row dense class="mb-4">
            <v-col cols="5">
              <v-text-field v-model="cfg.cookie_name" label="Cookie Name" placeholder="session" variant="outlined" density="compact"></v-text-field>
            </v-col>
            <v-col cols="7">
              <v-text-field v-model="cfg.cookie_value" label="Cookie Value" type="password" variant="outlined" density="compact"></v-text-field>
            </v-col>
          </v-row>

          <!-- API Key -->
          <v-divider class="mb-4"></v-divider>
          <p class="text-caption font-weight-bold text-uppercase text-grey-darken-1 mb-3">API Key</p>
          <v-row dense>
            <v-col cols="5">
              <v-text-field v-model="cfg.api_key_name" label="Key Name" placeholder="X-API-Key" variant="outlined" density="compact"></v-text-field>
            </v-col>
            <v-col cols="4">
              <v-text-field v-model="cfg.api_key_value" label="Key Value" type="password" variant="outlined" density="compact"></v-text-field>
            </v-col>
            <v-col cols="3">
              <v-select
                v-model="cfg.api_key_location"
                label="In"
                :items="['header', 'query']"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>
          </v-row>

        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Scan Options -->
    <v-expansion-panels variant="accordion" class="mb-6">
      <v-expansion-panel rounded="xl" elevation="0" class="form-card">
        <v-expansion-panel-title class="pa-6">
          <div class="d-flex align-center">
            <v-icon icon="mdi-tune-variant" color="primary" class="mr-2"></v-icon>
            <span class="text-subtitle-1 font-weight-bold text-slate-800">Scan Configuration</span>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text class="px-6 pb-6">

          <p class="text-caption font-weight-bold text-uppercase text-grey-darken-1 mb-3">Scan Modes</p>
          <v-row dense class="mb-4">
            <v-col cols="6">
              <v-checkbox v-model="cfg.time_analysis" label="Time-based injection" density="compact" color="primary" hide-details></v-checkbox>
            </v-col>
            <v-col cols="6">
              <v-checkbox v-model="cfg.enumerate_mode" label="Enumerate endpoints" density="compact" color="primary" hide-details></v-checkbox>
            </v-col>
            <v-col cols="6">
              <v-checkbox v-model="cfg.cors_mode" label="CORS misconfig check" density="compact" color="primary" hide-details></v-checkbox>
            </v-col>
            <v-col cols="6">
              <v-checkbox v-model="cfg.header_check_mode" label="Security headers" density="compact" color="primary" hide-details></v-checkbox>
            </v-col>
            <v-col cols="12">
              <v-checkbox v-model="cfg.ratelimit_mode" label="Rate-limit resilience" density="compact" color="primary" hide-details></v-checkbox>
            </v-col>
          </v-row>

          <v-text-field
            v-if="cfg.ratelimit_mode"
            v-model.number="cfg.ratelimit_burst_count"
            label="Burst Request Count"
            type="number"
            :min="1"
            :max="100"
            variant="outlined"
            density="compact"
            class="mb-4"
            style="max-width: 180px"
          ></v-text-field>

          <v-divider class="mb-4"></v-divider>
          <p class="text-caption font-weight-bold text-uppercase text-grey-darken-1 mb-3">Performance</p>

          <v-row dense>
            <v-col cols="6">
              <v-text-field
                v-model.number="cfg.max_concurrency"
                label="Max Concurrency"
                type="number"
                :min="1"
                :max="20"
                variant="outlined"
                density="compact"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="cfg.request_delay_ms"
                label="Delay (ms)"
                type="number"
                :min="0"
                variant="outlined"
                density="compact"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-text-field
            v-model="cfg.custom_wordlist"
            label="Custom Wordlist"
            placeholder="/admin,/debug,/health"
            hint="Comma-separated extra paths for enumeration"
            persistent-hint
            variant="outlined"
            density="compact"
            class="mt-2"
          ></v-text-field>

        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Submit -->
    <v-btn
      type="submit"
      block
      size="x-large"
      color="primary"
      class="scan-btn"
    >
      <v-icon icon="mdi-radar" class="mr-2"></v-icon>
      Start API Scan
    </v-btn>
  </v-form>
</template>

<style scoped>
.form-card {
  background: white;
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.section-label {
  display: flex;
  align-items: center;
}

.drop-zone {
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 12px;
  cursor: pointer;
  background: rgba(102, 126, 234, 0.02);
  transition: all 0.2s ease;
  min-height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}

.drop-zone:hover {
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(102, 126, 234, 0.05);
}

.drop-zone--error {
  border-color: rgb(var(--v-theme-error));
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.1);
}

.scan-btn {
  border-radius: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.3);
}
</style>
