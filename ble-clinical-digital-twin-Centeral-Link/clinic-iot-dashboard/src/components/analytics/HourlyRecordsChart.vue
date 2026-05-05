<script setup lang="ts">
import type ApexCharts from 'apexcharts';
import type { HourlyRecord } from '../../utils/types';
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const props = defineProps<{
  data: HourlyRecord[]
}>()

const categories = computed(() => props.data.map(d => {
  const date = new Date(d.hour)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}))

const series = computed(() => [{
  name: 'Records',
  data: props.data.map(d => d.records_count)
}])

const chartOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'area',
    background: 'transparent',
    toolbar: { show: false },
    sparkline: { enabled: false },
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  colors: ['#7C3AED'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.55,
      opacityTo: 0.05,
      stops: [0, 100],
      colorStops: [
        { offset: 0, color: '#7C3AED', opacity: 0.55 },
        { offset: 100, color: '#7C3AED', opacity: 0.03 }
      ]
    }
  },
  stroke: {
    curve: 'smooth',
    width: 2,
    dashArray: 5,
    colors: ['#A855F7']
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
      style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' }
    }
  },
  tooltip: {
    theme: 'dark',
    style: { fontFamily: 'monospace' },
    x: { show: true },
    y: { formatter: (val: number) => `${val} records` }
  },
  markers: { size: 0 },
  dataLabels: { enabled: false }
}))
</script>

<template>
  <div class="bg-[#0F1923] rounded-2xl p-6 border border-[#1A2535]">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-white font-semibold text-lg tracking-wide">Hourly Records</h2>
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block"></span>
        <span class="text-[#4B5A6E] text-xs font-mono">Records Count</span>
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
