<script setup lang="ts">
import type ApexCharts from 'apexcharts';
import type { HourlyPatient } from '../../utils/types';
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'


const props = defineProps<{
  data: HourlyPatient[]
}>()

const categories = computed(() => props.data.map(d => {
  const date = new Date(d.hour)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}))

const series = computed(() => [{
  name: 'Patients',
  data: props.data.map(d => d.patients_count)
}])

const chartOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  colors: ['#38BDF8'],
  plotOptions: {
    bar: {
      borderRadius: 6,
      columnWidth: '50%',
      colors: {
        ranges: [{
          from: 0,
          to: Infinity,
          color: undefined
        }],
        backgroundBarColors: ['#1A2535'],
        backgroundBarRadius: 6,
        backgroundBarOpacity: 1
      }
    }
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'vertical',
      shadeIntensity: 0.3,
      gradientToColors: ['#7C3AED'],
      inverseColors: false,
      opacityFrom: 0.95,
      opacityTo: 0.7
    }
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
    y: { formatter: (val: number) => `${val} patients` }
  },
  dataLabels: { enabled: false }
}))
</script>

<template>
  <div class="bg-[#0F1923] rounded-2xl p-6 border border-[#1A2535]">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-white font-semibold text-lg tracking-wide">Peak User Activity</h2>
      <div class="flex items-center gap-2 bg-[#1A2535] px-3 py-1.5 rounded-lg cursor-pointer select-none">
        <span class="text-[#8CA0B8] text-xs font-mono">Last Hours</span>
        <svg class="w-3.5 h-3.5 text-[#8CA0B8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
    <VueApexCharts
      type="bar"
      height="220"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>
