<script setup lang="ts">
import type { RouterMapEntry } from '../../utils/types';


const props = defineProps<{entries: RouterMapEntry[]}>();

/**
 * Calculates circle size based on device count.
 * Returns a value in pixels.
 */
const getCircleSize = (count: number) => {
  // Base size of 12px, plus growth based on count, capped at 40px
  return Math.min(12 + count * 2, 40);
};

/**
 * Helper to format percentage for CSS
 */
const toPercent = (val: number) => `${val * 100}%`;
</script>

<template>
  <div class="flex flex-col w-full h-125 bg-[#0b1120] rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
    <div class="flex items-center justify-between px-6 py-4 bg-[#0f172a]/80 backdrop-blur-sm border-b border-slate-800">
      <div class="flex items-center gap-2 text-white font-semibold">
        <Map :size="20" class="text-sky-500" />
        <span>Live Map - User Clusters</span>
      </div>
      
      <div class="flex p-1 bg-[#1e293b] rounded-lg">
        <button class="px-4 py-1.5 text-xs font-bold rounded-md bg-sky-500/20 text-sky-400 border border-sky-500/30">
          Real-time
        </button>
      </div>
    </div>

    <div class="relative grow bg-[#2d333e] m-4 rounded-lg overflow-hidden cursor-crosshair">
      <div class="absolute inset-0 opacity-5 pointer-events-none" 
           style="background-image: radial-gradient(#fff 1px, transparent 1px); background-size: 30px 30px;">
      </div>

      <div 
        v-for="entry in entries" 
        :key="entry.id"
        class="absolute -translate-x-1/2 -translate-y-1/2 group"
        :style="{ 
          left: toPercent(entry.location_x), 
          top: toPercent(entry.location_y) 
        }"
      >
        <div 
          class="relative rounded-full bg-sky-500 transition-all duration-500 ease-out"
          :style="{ 
            width: getCircleSize(entry.connected_devices_count) + 'px', 
            height: getCircleSize(entry.connected_devices_count) + 'px',
            boxShadow: `0 0 ${getCircleSize(entry.connected_devices_count)}px rgba(14, 165, 233, 0.6)`
          }"
        >
          <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-[10px] text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 pointer-events-none">
            {{ entry.connected_devices_count }} Devices
          </div>
        </div>
      </div>

      <div class="absolute bottom-4 right-4 flex flex-col gap-1">
        <button class="p-2 bg-[#1e293b] hover:bg-slate-700 text-slate-400 rounded-t-md border border-slate-700 transition-colors">
          <Plus :size="18" />
        </button>
        <button class="p-2 bg-[#1e293b] hover:bg-slate-700 text-slate-400 rounded-b-md border-x border-b border-slate-700 transition-colors">
          <Minus :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth pulsing animation for the dots */
@keyframes pulse-glow {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.bg-sky-500 {
  animation: pulse-glow 3s ease-in-out infinite;
}
</style>