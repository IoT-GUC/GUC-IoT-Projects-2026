<script setup lang="ts">
import type ApexCharts from 'apexcharts';
import type { RouterHourlySession } from '../../utils/types';
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'


const props = defineProps<{
  data: RouterHourlySession[]
  routerName?: string
}>()

const toMinutes = (seconds: number) => Math.round(seconds / 60)

const categories = computed(() => {
  const hours = [...new Set(props.data.map(d => d.hour))].sort()
  return hours.map(h => {
    const date = new Date(h)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  })
})

const series = computed(() => {
  const hours = [...new Set(props.data.map(d => d.hour))].sort()
  return [
    {
      name: 'Sessions',
      type: 'bar',
      data: hours.map(h => {
        const entry = props.data.find(d => d.hour === h)
        return entry ? entry.sessions_count : 0
      })
    },
    {
      name: 'Avg Duration (min)',
      type: 'line',
      data: hours.map(h => {
        const entry = props.data.find(d => d.hour === h)
        return entry ? toMinutes(entry.average_session_duration) : 0
      })
    }
  ]
})

const chartOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'line',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  colors: ['#3B82F6', '#A855F7'],
  plotOptions: {
    bar: {
      borderRadius: 5,
      columnWidth: '45%',
      colors: {
        backgroundBarColors: ['#1A2535'],
        backgroundBarRadius: 5,
        backgroundBarOpacity: 1
      }
    }
  },
  fill: {
    opacity: [0.85, 1],
    type: ['gradient', 'solid'],
    gradient: {
      shade: 'dark',
      type: 'vertical',
      shadeIntensity: 0.3,
      opacityFrom: 0.9,
      opacityTo: 0.5
    }
  },
  stroke: {
    width: [0, 2.5],
    curve: 'smooth',
    dashArray: [0, 0]
  },
  grid: {
    borderColor: '#1E2A3A',
    strokeDashArray: 4,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
    padding: { left: 10, right: 10 }
  },
  xaxis: {
    categories: categories.value,
    labels: {
      style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: [
    {
      title: {
        text: 'Sessions',
        style: { color: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' }
      },
      labels: {
        style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' }
      }
    },
    {
      opposite: true,
      title: {
        text: 'Avg Duration (min)',
        style: { color: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' }
      },
      labels: {
        style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' },
        formatter: (val: number) => `${val}m`
      }
    }
  ],
  tooltip: {
    theme: 'dark',
    style: { fontFamily: 'monospace' },
    shared: true,
    intersect: false,
    y: [
      { formatter: (val: number) => `${val} sessions` },
      { formatter: (val: number) => `${val} min` }
    ]
  },
  legend: {
    labels: { colors: '#8CA0B8' },
    fontFamily: 'monospace',
    fontSize: '12px',
    markers: { size: 10, radius: 50 }
  },
  markers: {
    size: [0, 4],
    colors: ['#A855F7'],
    strokeColors: '#0F1923',
    strokeWidth: 2,
    hover: { size: 6 }
  },
  dataLabels: { enabled: false }
}))
</script>

<template>
  <div class="bg-[#0F1923] rounded-2xl p-6 border border-[#1A2535]">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-white font-semibold text-lg tracking-wide">Router Hourly Sessions</h2>
        <p v-if="routerName" class="text-[#4B5A6E] text-xs font-mono mt-0.5">{{ routerName }}</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-sm bg-blue-500 inline-block"></span>
          <span class="text-[#4B5A6E] text-xs font-mono">Sessions</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-5 h-0.5 bg-purple-500 inline-block rounded-full"></span>
          <span class="text-[#4B5A6E] text-xs font-mono">Avg Duration</span>
        </div>
      </div>
    </div>
    <VueApexCharts
      type="line"
      height="240"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>
