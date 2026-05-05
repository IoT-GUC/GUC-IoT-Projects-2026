<script setup lang="ts">
import type ApexCharts from 'apexcharts';
import type { PatientSession } from '../../utils/types';
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'


const props = defineProps<{
  data: PatientSession[]
  patientName?: string
}>()

const formatTime = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const h = Math.floor(m / 60)
  const rem = m % 60
  return h > 0 ? `${h}h ${rem}m` : `${m}m`
}

// Group by router and sum durations
const routerGroups = computed(() => {
  const map: Record<string, { name: string; totalDuration: number; count: number }> = {}
  props.data.forEach(s => {
    if (!map[s.router_id]) {
      map[s.router_id] = { name: s.router_name, totalDuration: 0, count: 0 }
    }
    map[s.router_id]!.totalDuration += s.duration
    map[s.router_id]!.count += 1
  })
  return Object.values(map).sort((a, b) => b.totalDuration - a.totalDuration)
})

const donutSeries = computed(() => routerGroups.value.map(r => Math.round(r.totalDuration / 60)))
const donutLabels = computed(() => routerGroups.value.map(r => r.name))

const totalDuration = computed(() => props.data.reduce((sum, s) => sum + s.duration, 0))

const timelineSeries = computed(() => [{
  name: 'Duration (min)',
  data: [...props.data]
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .map(s => ({
      x: new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      y: Math.round(s.duration / 60),
      router: s.router_name
    }))
}])

const timelineOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  plotOptions: {
    bar: {
      borderRadius: 5,
      horizontal: true,
      barHeight: '55%',
      distributed: true,
      colors: {
        backgroundBarColors: ['#1A2535'],
        backgroundBarRadius: 5,
        backgroundBarOpacity: 1
      }
    }
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'horizontal',
      shadeIntensity: 0.3,
      gradientToColors: ['#7C3AED'],
      opacityFrom: 0.9,
      opacityTo: 0.6
    }
  },
  colors: ['#38BDF8', '#7C3AED', '#34D399', '#F59E0B', '#F87171', '#A78BFA'],
  grid: {
    borderColor: '#1E2A3A',
    strokeDashArray: 4,
    xaxis: { lines: { show: true } },
    yaxis: { lines: { show: false } },
    padding: { left: 0, right: 10 }
  },
  xaxis: {
    labels: {
      style: { colors: '#4B5A6E', fontFamily: 'monospace', fontSize: '11px' },
      formatter: (val: number) => `${val}m`
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: {
      style: { colors: '#8CA0B8', fontFamily: 'monospace', fontSize: '11px' }
    }
  },
  tooltip: {
    theme: 'dark',
    style: { fontFamily: 'monospace' },
    y: {
      formatter: (val: number, opts: any) => {
        const router = timelineSeries.value[0]?.data[opts.dataPointIndex]?.router ?? ''
        return `${val} min · ${router}`
      },
      title: { formatter: () => 'Session' }
    }
  },
  legend: { show: false },
  dataLabels: { enabled: false }
}))

const donutOptions = computed<ApexCharts.ApexOptions>(() => ({
  chart: {
    type: 'donut',
    background: 'transparent',
    animations: { enabled: true, speed: 800 }
  },
  theme: { mode: 'dark' },
  colors: ['#38BDF8', '#7C3AED', '#34D399', '#F59E0B', '#F87171', '#A78BFA'],
  labels: donutLabels.value,
  stroke: { width: 0 },
  plotOptions: {
    pie: {
      donut: {
        size: '68%',
        labels: {
          show: true,
          name: {
            show: true,
            fontSize: '12px',
            fontFamily: 'monospace',
            color: '#8CA0B8'
          },
          value: {
            show: true,
            fontSize: '20px',
            fontFamily: 'monospace',
            color: '#FFFFFF',
            formatter: (val: number) => `${val}m`
          },
          total: {
            show: true,
            label: 'Total',
            fontSize: '11px',
            fontFamily: 'monospace',
            color: '#4B5A6E',
            formatter: () => formatTime(totalDuration.value)
          }
        }
      }
    }
  },
  legend: {
    position: 'bottom',
    fontFamily: 'monospace',
    fontSize: '11px',
    labels: { colors: '#8CA0B8' },
    markers: { size: 8, radius: 50 }
  },
  tooltip: {
    theme: 'dark',
    style: { fontFamily: 'monospace' },
    y: { formatter: (val: number) => `${val} min` }
  },
  dataLabels: { enabled: false }
}))
</script>

<template>
  <div class="bg-[#0F1923] rounded-2xl p-6 border border-[#1A2535]">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-white font-semibold text-lg tracking-wide">Patient Sessions</h2>
        <p v-if="patientName" class="text-[#4B5A6E] text-xs font-mono mt-0.5">{{ patientName }}</p>
        <p class="text-[#4B5A6E] text-xs font-mono mt-0.5">
          {{ data.length }} sessions · Total {{ formatTime(totalDuration) }}
        </p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- Donut: time per router -->
      <div class="lg:col-span-2">
        <p class="text-[#4B5A6E] text-xs font-mono mb-3 uppercase tracking-widest">Time by Router</p>
        <VueApexCharts
          type="donut"
          height="240"
          :options="donutOptions"
          :series="donutSeries"
        />
      </div>

      <!-- Timeline bar chart -->
      <div class="lg:col-span-3">
        <p class="text-[#4B5A6E] text-xs font-mono mb-3 uppercase tracking-widest">Session Timeline</p>
        <VueApexCharts
          type="bar"
          height="240"
          :options="timelineOptions"
          :series="timelineSeries"
        />
      </div>
    </div>
  </div>
</template>
