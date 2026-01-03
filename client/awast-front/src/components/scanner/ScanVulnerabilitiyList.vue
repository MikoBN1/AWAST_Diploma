<script setup lang="ts">
import { ref } from 'vue'

interface Vulnerability {
  id: number
  severity: 'critical' | 'high' | 'medium' | 'low'
  cveId: string
  title: string
  description: string
  solution: string
  method: string
}

// Mock data with different severities
const vulnerabilities = ref<Vulnerability[]>([
  {
    id: 1,
    severity: 'critical',
    cveId: 'OWASP_2021_A01',
    title: 'SQL Injection in User Authentication',
    description: 'Unsanitized user input directly concatenated to SQL query',
    solution: 'Use parameterized queries or prepared statements. Never concatenate user input directly into SQL queries. Implement input validation and sanitization.',
    method: 'GET'
  },
  {
    id: 2,
    severity: 'high',
    cveId: 'OWASP_2021_A05',
    title: 'Security Misconfiguration - Missing Headers',
    description: 'Missing Content-Security-Policy and X-Frame-Options headers',
    solution: 'Modern Web browsers support the Content-Security-Policy and X-Frame-Options HTTP headers. Ensure one of them is set on all web pages returned by your site/app.',
    method: 'POST'
  },
  {
    id: 3,
    severity: 'medium',
    cveId: 'OWASP_2021_A03',
    title: 'Cross-Site Scripting (XSS) Vulnerability',
    description: 'User input rendered without proper escaping',
    solution: 'Implement proper output encoding and use Content Security Policy headers. Validate and sanitize all user inputs.',
    method: 'GET'
  }
])

const expandedItems = ref<Set<number>>(new Set())

const toggleExpand = (id: number) => {
  if (expandedItems.value.has(id)) {
    expandedItems.value.delete(id)
  } else {
    expandedItems.value.add(id)
  }
}

const getSeverityConfig = (severity: string) => {
  const configs = {
    critical: {
      icon: 'mdi-alert-octagon',
      gradient: 'linear-gradient(135deg, #ff0844 0%, #ff6b9d 100%)',
      color: '#ff0844',
      textColor: '#fff'
    },
    high: {
      icon: 'mdi-alert',
      gradient: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
      color: '#ff6b35',
      textColor: '#fff'
    },
    medium: {
      icon: 'mdi-alert-circle',
      gradient: 'linear-gradient(135deg, #ffd93d 0%, #f6c244 100%)',
      color: '#ffd93d',
      textColor: '#2c3e50'
    },
    low: {
      icon: 'mdi-information',
      gradient: 'linear-gradient(135deg, #6bcf7f 0%, #4facfe 100%)',
      color: '#6bcf7f',
      textColor: '#fff'
    }
  }
  return configs[severity as keyof typeof configs] || configs.low
}
</script>

<template>
  <div class="vulnerabilities-section">
    <div class="section-header">
      <div class="header-content">
        <v-icon class="header-icon" size="32">mdi-shield-alert</v-icon>
        <div>
          <h2 class="section-title">Security Vulnerabilities</h2>
          <p class="section-subtitle">Latest security issues detected in your codebase</p>
        </div>
      </div>
      <div class="stats-badge">
        <span class="stats-number">{{ vulnerabilities.length }}</span>
        <span class="stats-label">Issues Found</span>
      </div>
    </div>

    <div class="vulnerabilities-list">
      <div
        v-for="vuln in vulnerabilities"
        :key="vuln.id"
        class="vuln-card"
        :class="{ 'expanded': expandedItems.has(vuln.id) }"
      >
        <!-- Severity Badge Overlay -->
        <div 
          class="severity-badge"
          :class="`severity-badge-${vuln.severity}`"
        >
          <v-icon 
            :class="`severity-icon-${vuln.severity}`"
            size="20"
          >
            {{ getSeverityConfig(vuln.severity).icon }}
          </v-icon>
          <span 
            class="severity-text"
            :class="`severity-text-${vuln.severity}`"
          >
            {{ vuln.severity.toUpperCase() }}
          </span>
        </div>

        <!-- CVE Info -->
        <div class="cve-badge">
          <v-icon size="14" class="mr-1">mdi-identifier</v-icon>
          {{ vuln.cveId }}
        </div>

        <!-- Main Content -->
        <div class="vuln-content">
          <h3 class="vuln-title">{{ vuln.title }}</h3>
          
          <div class="vuln-description">
            <v-icon size="16" class="mr-2" color="#718096">mdi-text-box-outline</v-icon>
            <span>{{ vuln.description }}</span>
          </div>

          <!-- Expandable Solution Section -->
          <div v-if="expandedItems.has(vuln.id)" class="solution-section">
              <div class="solution-header">
                <v-icon size="18" color="#10b981">mdi-lightbulb-on</v-icon>
                <span class="solution-label">Recommended Solution</span>
              </div>
              <p class="solution-text">{{ vuln.solution }}</p>
            </div>

          <!-- Footer Actions -->
          <div class="vuln-footer">
            <div class="method-badge">
              <v-icon size="14" class="mr-1">mdi-api</v-icon>
              {{ vuln.method }}
            </div>
            
            <div class="action-buttons">
              <v-btn
                size="small"
                variant="text"
                class="details-btn"
                @click="toggleExpand(vuln.id)"
              >
                <v-icon size="18" class="mr-1">
                  {{ expandedItems.has(vuln.id) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                </v-icon>
                {{ expandedItems.has(vuln.id) ? 'Less' : 'More' }} Details
              </v-btn>
              
              <v-btn
                size="small"
                class="exploit-btn"
                :class="`exploit-btn-${vuln.severity}`"
              >
                <v-icon size="18" class="mr-1">mdi-bug-play</v-icon>
                Exploit
              </v-btn>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vulnerabilities-section {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-radius: 16px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  color: #6366f1;
  opacity: 0.9;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  line-height: 1.2;
}

.section-subtitle {
  font-size: 14px;
  color: #718096;
  margin: 4px 0 0 0;
}

.stats-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.stats-number {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.stats-label {
  font-size: 12px;
  color: #718096;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Vulnerabilities List */
.vulnerabilities-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Vulnerability Card */
.vuln-card {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(203, 213, 225, 0.6);
  border-radius: 20px;
  padding: 24px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  overflow: hidden;
  will-change: transform;
  transform: translateZ(0);
}

.vuln-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.vuln-card:hover {
  transform: translateY(-4px) translateZ(0);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-color: rgba(99, 102, 241, 0.4);
}

.vuln-card:hover::before {
  opacity: 1;
}

.vuln-card.expanded {
  box-shadow: 0 12px 24px rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
}

/* Severity Badge */
.severity-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 2;
  transition: transform 0.3s ease;
}

.vuln-card:hover .severity-badge {
  transform: scale(1.05);
}

.severity-badge-critical {
  background: linear-gradient(135deg, #ff0844 0%, #ff6b9d 100%);
}

.severity-badge-high {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
}

.severity-badge-medium {
  background: linear-gradient(135deg, #ffd93d 0%, #f6c244 100%);
}

.severity-badge-low {
  background: linear-gradient(135deg, #6bcf7f 0%, #4facfe 100%);
}

.severity-icon-critical,
.severity-icon-high,
.severity-icon-low {
  color: #fff;
}

.severity-icon-medium {
  color: #2c3e50;
}

.severity-text-critical,
.severity-text-high,
.severity-text-low {
  color: #fff;
}

.severity-text-medium {
  color: #2c3e50;
}

.severity-text {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* CVE Badge */
.cve-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 16px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

/* Content */
.vuln-content {
  margin-right: 140px;
}

.vuln-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 12px 0;
  line-height: 1.3;
}

.vuln-description {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #4a5568;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(113, 128, 150, 0.05);
  border-radius: 8px;
  border-left: 3px solid rgba(99, 102, 241, 0.3);
}

/* Solution Section */
.solution-section {
  margin: 16px 0;
  padding: 16px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.solution-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.solution-label {
  font-size: 14px;
  font-weight: 700;
  color: #059669;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.solution-text {
  color: #2d3748;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

/* Expand Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease-out;
  max-height: 300px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Footer */
.vuln-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(203, 213, 225, 0.4);
}

.method-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: rgba(71, 85, 105, 0.1);
  color: #475569;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(71, 85, 105, 0.2);
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.details-btn {
  color: #6366f1 !important;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0;
  transition: all 0.2s ease;
}

.details-btn:hover {
  background: rgba(99, 102, 241, 0.1) !important;
}

.exploit-btn {
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.exploit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.exploit-btn-critical {
  background: linear-gradient(135deg, #ff0844 0%, #ff6b9d 100%);
  color: #fff;
}

.exploit-btn-high {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  color: #fff;
}

.exploit-btn-medium {
  background: linear-gradient(135deg, #ffd93d 0%, #f6c244 100%);
  color: #2c3e50;
}

.exploit-btn-low {
  background: linear-gradient(135deg, #6bcf7f 0%, #4facfe 100%);
  color: #fff;
}

/* Responsive Design */
@media (max-width: 768px) {
  .vulnerabilities-section {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .vuln-content {
    margin-right: 0;
    margin-top: 60px;
  }

  .severity-badge {
    top: 12px;
    right: 12px;
  }

  .vuln-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .action-buttons {
    width: 100%;
    justify-content: space-between;
  }
}
</style>