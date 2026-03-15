<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore';
import { storeToRefs } from 'pinia';
import { onMounted, computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '@/stores/scanStore';

const authStore = useAuthStore();
const scanStore = useScanStore();
const router = useRouter();
const { user } = storeToRefs(authStore);
const { scanStatus, scanHistory } = storeToRefs(scanStore);

onMounted(async () => {
  await Promise.all([
    authStore.fetchProfile(),
    scanStore.fetchAlertsSummary(),
    scanStore.fetchScanHistory(),
  ]);
});

// Alerts summary: support both ZAP shape (summary.alertsSummary) and flat (summary.High)
const alertsSummary = computed(() => {
  const s = scanStatus.value?.summary;
  return s?.alertsSummary ?? s ?? null;
});

const displayName = computed(() => user.value?.username ?? 'User');
const roleLabel = computed(() => {
  const r = user.value?.role ?? '';
  return r === 'admin' ? 'ADMINISTRATOR' : (r ? r.toUpperCase() : 'USER');
});
const profileDescription = computed(() =>
  user.value?.role === 'admin'
    ? 'Overseeing infrastructure security audits and automated vulnerability assessments.'
    : 'Managing security scans and monitoring vulnerability posture.'
);

const activeFleetCount = computed(() => user.value?.enabled_domains?.length ?? 0);
const totalVulnerabilities = computed(() => {
  const s = alertsSummary.value;
  if (!s) return 0;
  return (s.High ?? 0) + (s.Medium ?? 0) + (s.Low ?? 0) + (s.Informational ?? 0);
});

const criticalHighCount = computed(() => alertsSummary.value?.High ?? 0);
const mediumCount = computed(() => alertsSummary.value?.Medium ?? 0);
const lowCount = computed(() => alertsSummary.value?.Low ?? 0);
const infoCount = computed(() => alertsSummary.value?.Informational ?? 0);

const totalForBars = computed(() =>
  Math.max(totalVulnerabilities.value, 1)
);
const criticalHighPercent = computed(() =>
  (criticalHighCount.value / totalForBars.value) * 100
);
const mediumPercent = computed(() =>
  (mediumCount.value / totalForBars.value) * 100
);

// Active Fleet trend: domains scanned in last 30 days (unique targets)
const thirtyDaysAgo = () => {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.getTime();
};
const recentScansCount = computed(() => {
  const list = scanHistory.value ?? [];
  const cutoff = thirtyDaysAgo();
  return list.filter((scan: { created_at?: string }) => {
    const t = scan.created_at ? new Date(scan.created_at).getTime() : 0;
    return t >= cutoff;
  }).length;
});
const activeFleetTrendText = computed(() => {
  const n = recentScansCount.value;
  if (n === 0) return 'No scans in the last 30 days';
  return `${n} scan${n !== 1 ? 's' : ''} in the last 30 days`;
});

const enabledDomainsWithTags = computed(() => {
  const domains = user.value?.enabled_domains ?? [];
  const tagSets: Record<string, string[]> = {
    'api.internal-node.sh': ['PRODUCTION', 'AWS'],
    'staging.internal-node.sh': ['STAGING', 'INTERNAL'],
    'legacy.internal-node.sh': ['LEGACY', 'HIGH RISK'],
    'auth.oauth.internal-node.sh': ['OAUTH', 'INTERNAL'],
  };
  return domains.map((d) => ({
    name: d,
    tags: tagSets[d] ?? (d.includes('api') ? ['PRODUCTION'] : ['INTERNAL']),
  }));
});

function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays === 1) return 'Yesterday, ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

interface ActivityItem {
  type: 'critical' | 'info';
  title: string;
  detail: string;
  linkText?: string;
  linkTo?: string;
  detailSuffix?: string;
  time: string;
}

const ACTIVITY_PAGE_SIZE = 5;
const activityLogPage = ref(1);

const activityLogItemsAll = computed<ActivityItem[]>(() => {
  const list = scanHistory.value ?? [];
  if (list.length === 0) {
    return [{
      type: 'info',
      title: 'No activity yet',
      detail: 'Run a security scan to see activity here.',
      time: '—',
    }];
  }
  return list.map((scan: { scan_id: string; target: string; created_at: string; status: string }) => {
    const status = scan.status ?? '';
    const isError = status === 'error' || status === 'stopped';
    const title = status === 'done'
      ? 'Scan completed'
      : isError
        ? 'Scan failed'
        : status === 'running' || status === 'pending'
          ? 'Scan in progress'
          : 'Scan completed';
    const hostname = scan.target ? (() => {
      try {
        const u = new URL(scan.target.startsWith('http') ? scan.target : `https://${scan.target}`);
        return u.hostname || scan.target;
      } catch {
        return scan.target;
      }
    })() : scan.target;
    return {
      type: isError ? 'critical' : 'info',
      title,
      detail: status === 'done' ? 'Security scan finished for ' : isError ? 'Scan did not complete for ' : 'Scan for ',
      linkText: hostname,
      linkTo: `/scanner/${scan.scan_id}`,
      time: formatRelativeTime(scan.created_at ?? new Date().toISOString()),
    };
  });
});

const activityLogTotalPages = computed(() =>
  Math.max(1, Math.ceil(activityLogItemsAll.value.length / ACTIVITY_PAGE_SIZE))
);

watch(activityLogTotalPages, (total) => {
  if (activityLogPage.value > total) activityLogPage.value = 1;
});

const paginatedActivityItems = computed<ActivityItem[]>(() => {
  const all = activityLogItemsAll.value;
  if (all.length === 0 || all[0]?.title === 'No activity yet') return all;
  const totalPages = activityLogTotalPages.value;
  const page = Math.min(Math.max(1, activityLogPage.value), totalPages);
  const start = (page - 1) * ACTIVITY_PAGE_SIZE;
  return all.slice(start, start + ACTIVITY_PAGE_SIZE);
});

const exportReport = () => {
  router.push({ name: 'scanner_history' });
};
const getFullAIAnalysis = () => {
  router.push({ name: 'swagger-analysis' });
};
</script>

<template>
  <v-container fluid class="pa-6">
    <template v-if="user">
      <v-sheet
        class="profile-header rounded-xl pa-6 mb-6"
        elevation="4"
      >
        <div class="d-flex flex-wrap align-center">
          <div class="position-relative mr-6 mb-4 mb-sm-0">
            <v-avatar size="100" color="surface" class="profile-avatar">
              <v-icon icon="mdi-account" size="56" color="primary"></v-icon>
            </v-avatar>
          </div>
          <div class="flex-grow-1">
            <div class="d-flex align-center flex-wrap gap-2 mb-2">
              <h1 class="text-h4 font-weight-bold text-white mr-2">{{ displayName }}</h1>
              <v-chip
                color="white"
                variant="elevated"
                elevation="1"
                size="small"
                class="text-uppercase font-weight-bold text-primary"
              >
                {{ roleLabel }}
              </v-chip>
            </div>
            <p class="text-body-2 text-white mb-4 opacity-90">
              {{ profileDescription }}
            </p>
            <div class="d-flex flex-wrap">
              <v-btn
                color="white"
                style="font-size: 15px;"
                variant="outlined"
                prepend-icon="mdi-history"
                class="header-btn"
                @click="exportReport"
              >
                Scan History
              </v-btn>
            </div>
          </div>
        </div>
      </v-sheet>

      <v-row>
        <v-col cols="12" lg="8">
          <v-row class="mb-4">
            <v-col cols="12" sm="6">
              <v-card class="pa-5 h-100 custom-card" rounded="xl" elevation="0">
                <div class="text-uppercase text-caption text-medium-emphasis font-weight-bold mb-2">
                  Active Fleet
                </div>
                <div class="d-flex align-center mb-1">
                  <v-icon icon="mdi-folder-outline" size="24" class="mr-3" color="primary"></v-icon>
                  <span class="text-h4 font-weight-black">{{ activeFleetCount }}</span>
                </div>
                <div class="text-body-2 text-medium-emphasis mb-2">Monitored Domains</div>
                <div class="d-flex align-center text-primary text-body-2 font-weight-medium">
                  <v-icon icon="mdi-chart-timeline-variant" size="18" class="mr-1"></v-icon>
                  <span>{{ activeFleetTrendText }}</span>
                </div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="6">
              <v-card class="pa-5 h-100 custom-card" rounded="xl" elevation="0">
                <div class="text-uppercase text-caption text-medium-emphasis font-weight-bold mb-2">
                  Security Debt
                </div>
                <div class="d-flex align-center mb-1">
                  <v-icon icon="mdi-alert" size="24" class="mr-3" color="error"></v-icon>
                  <span class="text-h4 font-weight-black">{{ totalVulnerabilities }}</span>
                </div>
                <div class="text-body-2 text-medium-emphasis mb-2">Total Vulnerabilities</div>
                <div class="d-flex align-center text-error text-body-2 font-weight-medium">
                  <v-icon icon="mdi-alert-circle" size="18" class="mr-1"></v-icon>
                  <span>Critical attention required</span>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <v-card class="pa-5 mb-4 custom-card" rounded="xl" elevation="0">
            <h3 class="text-subtitle-1 font-weight-bold mb-5">Vulnerability Distribution</h3>
            <div class="mb-5">
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2 font-weight-medium">Critical / High</span>
                <span class="font-weight-bold">{{ criticalHighCount }}</span>
              </div>
              <v-progress-linear
                :model-value="criticalHighPercent"
                color="error"
                height="8"
                rounded
              ></v-progress-linear>
            </div>
            <div class="mb-6">
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2 font-weight-medium">Medium Severity</span>
                <span class="font-weight-bold">{{ mediumCount }}</span>
              </div>
              <v-progress-linear
                :model-value="mediumPercent"
                color="orange-darken-2"
                height="8"
                rounded
              ></v-progress-linear>
            </div>
            <v-row>
              <v-col cols="6">
                <v-card variant="tonal" color="grey" class="pa-4 rounded-lg" elevation="0">
                  <div class="text-uppercase text-caption text-medium-emphasis font-weight-bold">Low Risk</div>
                  <div class="text-h5 font-weight-black mt-1">{{ lowCount }}</div>
                </v-card>
              </v-col>
              <v-col cols="6">
                <v-card variant="tonal" color="primary" class="pa-4 rounded-lg" elevation="0">
                  <div class="text-uppercase text-caption text-primary font-weight-bold">Informational</div>
                  <div class="text-h5 font-weight-black text-primary mt-1">{{ infoCount }}</div>
                </v-card>
              </v-col>
            </v-row>
          </v-card>

          <v-card class="pa-5 custom-card" rounded="xl" elevation="0">
            <div class="d-flex justify-space-between align-center mb-5">
              <h3 class="text-subtitle-1 font-weight-bold mb-0">Activity Log</h3>
            </div>
            <div class="activity-list">
              <div
                v-for="(item, i) in paginatedActivityItems"
                :key="i"
                class="activity-item d-flex align-start mb-5"
              >
                <v-icon
                  v-if="item.type === 'critical'"
                  icon="mdi-circle"
                  size="10"
                  color="error"
                  class="mt-1 mr-3"
                ></v-icon>
                <v-icon
                  v-else
                  icon="mdi-circle"
                  size="10"
                  color="success"
                  class="mt-1 mr-3"
                ></v-icon>
                <div class="flex-grow-1">
                  <div class="font-weight-bold mb-1">{{ item.title }}</div>
                  <div class="text-body-2 text-medium-emphasis">
                    {{ item.detail }}
                    <router-link
                      v-if="item.linkText"
                      :to="(item.linkTo ?? '/')"
                      class="text-primary text-decoration-none font-weight-medium mx-1"
                    >
                      {{ item.linkText }}
                    </router-link>
                    {{ item.detailSuffix ?? '' }}
                  </div>
                  <div class="text-caption text-medium-emphasis mt-2 d-flex align-center">
                    <v-icon icon="mdi-clock-outline" size="14" class="mr-1"></v-icon>
                    {{ item.time }}
                  </div>
                </div>
              </div>
            </div>
            <v-pagination
              v-if="activityLogTotalPages > 1"
              v-model="activityLogPage"
              :length="activityLogTotalPages"
              :total-visible="5"
              density="comfortable"
              class="mt-4"
              rounded
            ></v-pagination>
          </v-card>
        </v-col>

        <v-col cols="12" lg="4">
          <v-card class="pa-5 mb-4 custom-card" rounded="xl" elevation="0">
            <div class="d-flex justify-space-between align-center mb-5">
              <h3 class="text-subtitle-1 font-weight-bold mb-0">Enabled Domains</h3>
            </div>
            <div class="domain-list">
              <div
                v-for="(item, i) in enabledDomainsWithTags"
                :key="i"
                class="domain-item mb-4 pa-3 rounded-lg border"
              >
                <div class="d-flex align-center mb-2">
                  <v-icon icon="mdi-web" size="18" class="mr-2 text-primary"></v-icon>
                  <span class="font-weight-bold text-body-2">{{ item.name }}</span>
                </div>
                <div class="d-flex flex-wrap gap-1 ml-6">
                  <v-chip
                    v-for="tag in item.tags"
                    :key="tag"
                    size="x-small"
                    :color="tag === 'HIGH RISK' ? 'error' : tag === 'AWS' ? 'orange-darken-2' : 'grey-darken-1'"
                    :variant="tag === 'HIGH RISK' ? 'elevated' : 'tonal'"
                    class="text-caption font-weight-bold"
                  >
                    {{ tag }}
                  </v-chip>
                </div>
              </div>
            </div>
          </v-card>

          <v-card class="pa-6 swagger-ai-card rounded-xl" elevation="4">
            <div class="d-flex align-center mb-3">
              <v-icon icon="mdi-robot-outline" size="24" class="text-white opacity-90 mr-2"></v-icon>
              <h3 class="text-subtitle-1 font-weight-bold text-white mb-0">Swagger AI Insights</h3>
            </div>
            <p class="text-body-2 text-white opacity-90 mb-6 line-height-relaxed">
              Your current security posture has improved by <strong class="text-green-accent-2">12%</strong> since last month.
              {{ displayName }}, we recommend reviewing the outdated SSL certificates on the legacy dashboard.
            </p>
            <v-btn
              color="white"
              variant="elevated"
              class="text-primary font-weight-bold"
              block
              append-icon="mdi-arrow-right"
              @click="getFullAIAnalysis"
            >
              Get Full AI Analysis
            </v-btn>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <v-alert
      v-else
      type="warning"
      title="Profile Not Found"
      text="Unable to load user profile information."
      class="rounded-xl border"
      variant="tonal"
    ></v-alert>
  </v-container>
</template>

<style scoped>
/* Improved Gradient Banner */
.profile-header {
  background: linear-gradient(135deg, 
    rgb(var(--v-theme-primary)) 0%, 
    rgba(var(--v-theme-primary), 0.75) 50%, 
    rgba(var(--v-theme-primary), 0.95) 100%
  ) !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15) !important;
  position: relative;
  overflow: hidden;
}

/* Optional subtle background pattern for the banner */
.profile-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(circle at top right, rgba(255,255,255,0.1) 0%, transparent 40%);
  pointer-events: none;
}

.profile-avatar {
  border: 4px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.profile-avatar-gear {
  position: absolute;
  bottom: 0;
  right: 0;
  min-width: 32px;
  width: 32px;
  height: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.header-btn {
  border-color: rgba(255, 255, 255, 0.4) !important;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}
.header-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.8) !important;
}

/* Improved Card Borders and Hover States */
.custom-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  background-color: rgb(var(--v-theme-surface));
}

.custom-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
  box-shadow: 0 6px 16px -4px rgba(0, 0, 0, 0.05) !important;
  transform: translateY(-2px);
}

.domain-item {
  border-color: rgba(var(--v-theme-on-surface), 0.05) !important;
  background-color: rgba(var(--v-theme-on-surface), 0.01);
  transition: background-color 0.2s ease;
}

.domain-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
}

.custom-btn {
  border-width: 1px;
}

/* AI Insights Card Styling */
.swagger-ai-card {
  background: linear-gradient(145deg, #2d3748 0%, #1a202c 100%);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1) !important;
}

.line-height-relaxed {
  line-height: 1.6;
}

.activity-item:last-child {
  margin-bottom: 0 !important;
}
</style>
