<script setup lang="ts">
import { ref } from 'vue'
import SwaggerUpload from '../components/swagger/SwaggerUpload.vue'
import SwaggerFindingsList from '../components/swagger/SwaggerFindingsList.vue'
import { swaggerService } from '../services/swaggerService'

const isAnalyzing = ref(false)
const showResults = ref(false)
const results = ref<any[]>([])
const currentFile = ref<File | null>(null)

const handleAnalysis = async (file: File) => {
  currentFile.value = file
  isAnalyzing.value = true
  showResults.value = false
  
  try {
    const response = await swaggerService.analyzeSwagger(file)
    results.value = response.findings
    showResults.value = true
    
    // Scroll to results
    setTimeout(() => {
      const resultsElement = document.getElementById('results-section')
      if (resultsElement) {
        resultsElement.scrollIntoView({ behavior: 'smooth' })
      }
    }, 100)
  } catch (error) {
    console.error('Failed to analyze swagger file:', error)
  } finally {
    isAnalyzing.value = false
  }
}

const resetAnalysis = () => {
  showResults.value = false
  results.value = []
  currentFile.value = null
}
</script>

<template>
  <div class="analysis-container">
    <div class="header-section mb-8">
      <v-container>
        <div class="d-flex align-center justify-center flex-column text-center">
          <div class="icon-badge mb-4">
             <v-icon icon="mdi-api" size="48" color="primary"></v-icon>
          </div>
          <h1 class="text-h3 font-weight-bold text-white mb-2">Swagger Vulnerability AI</h1>
          <p class="text-subtitle-1 text-white opacity-90" style="max-width: 600px">
            Upload your OpenAPI/Swagger definition files to automatically detect security vulnerabilities, logical flaws, and compliance issues using advanced AI analysis.
          </p>
        </div>
      </v-container>
    </div>

    <v-container>
      <v-row justify="center">
        <v-col cols="12" md="8" lg="6">
          <SwaggerUpload 
            @analyze="handleAnalysis" 
            :class="{ 'disabled-upload': isAnalyzing }"
          />
        </v-col>
      </v-row>

      <v-row v-if="isAnalyzing" class="mt-8 justify-center">
        <v-col cols="12" md="8 text-center">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            width="6"
            class="mb-4"
          ></v-progress-circular>
          <h3 class="text-h5 font-weight-bold text-slate-700">Analyzing API Structure...</h3>
          <p class="text-body-1 text-grey-darken-1">AI is scanning your endpoints for security flaws</p>
        </v-col>
      </v-row>

      <div id="results-section" class="mt-8" v-if="showResults">
        <v-row justify="center">
          <v-col cols="12" md="10">
            <div class="d-flex justify-space-between align-center mb-4">
               <v-btn
                variant="text"
                prepend-icon="mdi-arrow-left"
                @click="resetAnalysis"
               >
                 Analyze Another File
               </v-btn>
            </div>
            
            <SwaggerFindingsList :findings="results" />
          </v-col>
        </v-row>
      </div>
    </v-container>
  </div>
</template>

<style scoped>
.analysis-container {
  min-height: 100vh;
  background-color: #f8fafc;
  padding-bottom: 60px;
}

.header-section {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  padding: 60px 0 80px;
  position: relative;
}

.header-section::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: #f8fafc;
  border-radius: 40px 40px 0 0;
}

.icon-badge {
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.disabled-upload {
  opacity: 0.7;
  pointer-events: none;
}
</style>
