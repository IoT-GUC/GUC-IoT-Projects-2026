<script setup lang="ts">
import type ApexCharts from 'apexcharts';
import type { HourlySessionDuration } from '../../utils/types';
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'


const props = defineProps<{
  data: HourlySessionDuration[]
}>()

const toMinutes = (seconds: number) => Math.round(seconds / 60)

const categories = computed(() => props.data.map(d => {
  const date = new Date(d.hour)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}))

const series = computed(() => [{
  name: 'Avg Duration',
  data: props.data.map(d => toMinutes(d.average_total_session_duration))
}])

const chartOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'area',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  colors: ['#34D399'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.45,
      opacityTo: 0.02,
      stops: [0, 100],
      colorStops: [
        { offset: 0, color: '#34D399', opacity: 0.45 },
        { offset: 100, color: '#34D399', opacity: 0.02 }
      ]
    }
  },
  stroke: {
    curve: 'smooth',
    width: 2.5,
    colors: ['#34D399']
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
  yaxis: {
    labels: {
      style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' },
      formatter: (val: number) => `${val}m`
    }
  },
  tooltip: {
    theme: 'dark',
    style: { fontFamily: 'monospace' },
    y: { formatter: (val: number) => `${val} min avg` }
  },
  markers: {
    size: 4,
    colors: ['#34D399'],
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
        <h2 class="text-white font-semibold text-lg tracking-wide">Avg Session Duration</h2>
        <p class="text-[#4B5A6E] text-xs font-mono mt-0.5">per hour · in minutes</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
        <span class="text-[#4B5A6E] text-xs font-mono">Global Avg</span>
      </div>
    </div>
    <VueApexCharts
      type="area"
      height="220"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>
