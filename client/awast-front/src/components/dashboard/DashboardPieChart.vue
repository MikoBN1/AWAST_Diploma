<script setup lang="ts">
import {Pie} from 'vue-chartjs'
import {ArcElement, Chart as ChartJS, Legend, Title, Tooltip} from 'chart.js'
import {computed} from "vue";

ChartJS.register(Title, Tooltip, Legend, ArcElement)

const props = defineProps({
  severityCounts: {
    type: Object,
  },
  width: {
    type: String,
    required: true
  }
})


const chartData = computed(() => {
  const styles = getComputedStyle(document.documentElement)
  const getColor = (key: string) => styles.getPropertyValue(key).trim()

  return {
    labels: ['High Severity', 'Medium Severity', 'Low Severity'],
    datasets: [
      {
        label: 'Vulnerability Distribution',
        data: [
          props.severityCounts?.high || 0,
          props.severityCounts?.medium || 0,
          props.severityCounts?.low || 0,
        ],
        backgroundColor: [
          getColor('--high-severity'),
          getColor('--medium-severity'),
          getColor('--low-severity'),
        ],
        borderColor: '#fff',
        borderWidth: 2,
      }
    ]
  }
})

function checkForAllZero(){
  const data = [
    props.severityCounts?.critical || 0,
    props.severityCounts?.high || 0,
    props.severityCounts?.medium || 0,
    props.severityCounts?.low || 0,
    props.severityCounts?.info || 0
  ]
  return data.every(item => item === 0)
}


const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        padding: 20,
      }
    },
    title: {
      display: false,
      text: 'Vulnerability Breakdown'
    }
  },
}
</script>

<template>
  <v-card :width="props.width" height="100%" class="rounded-xl border-thin" elevation="0">
    <v-card-text>
      <div class="pie-chart">
        <h1>Vulnerability Distribution</h1>
        <div v-if="!props.severityCounts" class="progress">
          <v-progress-circular
              color="primary"
              size="200"
              indeterminate
          ></v-progress-circular>
        </div>
        <div v-else-if="checkForAllZero()" class="no-vulns-wrapper">
          <h3>Not found</h3>
        </div>
        <Pie :data="chartData" :options="chartOptions"  v-else/>
      </div>
    </v-card-text>
  </v-card>
</template>
<style scoped>
.progress{
  display: flex;
  justify-content: center;
  align-items: center;
}
h1{
  font-size: 18px;
  line-height: 28px;
  font-weight: 600;
  color: var(--h1-color);
  text-align: center;
  margin-top: 0;
  margin-bottom: 16px;
}
.no-vulns-wrapper{
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
h3{
  font-size: 24px;
  color: var(--sub-text);
}
@media screen and (max-width: 1400px) {
  canvas{
    max-width: 500px;
    max-height: 500px;
  }
  .pie-chart{
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
  }
}
.border-thin {
   border: 1px solid rgba(0,0,0,0.05);
}
</style>