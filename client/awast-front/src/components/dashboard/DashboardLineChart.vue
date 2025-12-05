<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import {computed, type PropType} from 'vue'

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend)

interface ChartData {
  created_at: string
  count: number
}

const props = defineProps({
  items: {
    type: Array as PropType<ChartData[]>,
    required: true
  },
  width: {
    type: String,
    required: true
  }
})

const chartData = computed(() => {
  const labels = props.items.map(i => i.created_at)
  const dataValues = props.items.map(i => i.count)

  const styles = getComputedStyle(document.documentElement)
  const getColor = (key: string) => styles.getPropertyValue(key).trim()

  return {
    labels,
    datasets: [
      {
        label: 'Count',
        data: dataValues,
        borderWidth: 2,
        borderColor: "#3498DB",
        backgroundColor: "#3498DB",
        fill: false,
        tension: 0.2
      }
    ]
  }
})

function checkForAllZero() {
  if (!props.items || props.items.length === 0) return true
  return props.items.every(i => i.count === 0)
}

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'bottom'
    }
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'day'
      }
    },
    y: {
      beginAtZero: true
    }
  }
}
</script>

<template>
  <v-card>
    <v-card-text>
      <div class="line-chart">
        <h1>Scans Timeline</h1>

        <div v-if="!props.items" class="progress">
          <v-progress-circular
              color="primary"
              size="200"
              indeterminate
          ></v-progress-circular>
        </div>

        <div v-else-if="checkForAllZero()" class="no-vulns-wrapper">
          <h3>Not found</h3>
        </div>

        <Line v-else :data="chartData" :options="chartOptions" />
      </div>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.progress {
  display: flex;
  justify-content: center;
  align-items: center;
}

h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--h1-color);
  text-align: center;
  margin-top: 0;
  margin-bottom: 16px;
}

.no-vulns-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

h3 {
  font-size: 24px;
  color: var(--sub-text);
}

@media screen and (max-width: 1400px) {
  canvas {
    max-width: 500px;
    max-height: 500px;
  }

  .line-chart {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
  }
}
</style>
