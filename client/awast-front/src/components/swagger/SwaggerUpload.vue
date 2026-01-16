<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits(['analyze'])

const file = ref<File | undefined>(undefined)
const loading = ref(false)
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    file.value = target.files[0]
    error.value = ''
  }
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    file.value = event.dataTransfer.files[0]
    error.value = ''
  }
}

const validateFile = (file: File) => {
  const validExtensions = ['.json', '.yaml', '.yml']
  const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  return validExtensions.includes(extension)
}

const startAnalysis = async () => {
  if (!file.value) return
  
  if (!validateFile(file.value)) {
    error.value = 'Please upload a valid Swagger/OpenAPI file (.json, .yaml, .yml)'
    return
  }

  loading.value = true
  // Simulate reading the file content if needed, currently passing the file object
  // In a real scenario, we might read user content here or send formData
  
  // Emit event to parent to handle the "API call" / mock logic
  emit('analyze', file.value)
  loading.value = false
}
</script>

<template>
  <v-card class="upload-card" elevation="0">
    <v-card-text class="pa-8 text-center">
      <div 
        class="drop-zone mb-6"
        @dragover.prevent
        @drop="onDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          class="d-none"
          accept=".json,.yaml,.yml"
          @change="handleFileChange"
        >
        
        <div v-if="!file" class="upload-placeholder">
          <div class="icon-wrapper mb-4">
            <v-icon icon="mdi-cloud-upload" size="40" color="primary"></v-icon>
          </div>
          <h3 class="text-h6 font-weight-bold text-slate-800 mb-2">Upload Swagger File</h3>
          <p class="text-body-2 text-grey-darken-1 mb-0">
            Drag & drop your OpenAPI/Swagger definition here<br>
            or click to browse
          </p>
          <div class="mt-4">
             <v-chip size="small" color="primary" variant="outlined" class="mr-2">.json</v-chip>
             <v-chip size="small" color="primary" variant="outlined">.yaml</v-chip>
          </div>
        </div>

        <div v-else class="file-preview">
          <v-icon icon="mdi-file-code" size="48" color="primary" class="mb-3"></v-icon>
          <div class="text-h6 font-weight-bold text-slate-800">{{ file.name }}</div>
          <div class="text-caption text-grey-darken-1">{{ (file.size / 1024).toFixed(2) }} KB</div>
          <v-btn
            variant="text"
            color="error"
            size="small"
            class="mt-2"
            @click.stop="file = undefined"
          >
            Remove
          </v-btn>
        </div>
      </div>

      <v-alert
        v-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
        closable
      >
        {{ error }}
      </v-alert>

      <v-btn
        block
        size="x-large"
        color="primary"
        class="analyze-btn"
        :loading="loading"
        :disabled="!file"
        @click="startAnalysis"
      >
        <v-icon icon="mdi-shield-search" class="mr-2"></v-icon>
        Analyze Vulnerabilities
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.upload-card {
  background: white;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.drop-zone {
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 40px;
  cursor: pointer;
  background: rgba(102, 126, 234, 0.02);
}

.drop-zone:hover {
  border-color: rgba(102, 126, 234, 0.6);
  background: rgba(102, 126, 234, 0.05);
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.1);
}

.analyze-btn {
  border-radius: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.analyze-btn:not(:disabled):hover {
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
}
</style>
