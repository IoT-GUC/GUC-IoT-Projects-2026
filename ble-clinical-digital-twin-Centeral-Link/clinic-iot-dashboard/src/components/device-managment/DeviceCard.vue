<template>
  <div class="relative w-72 bg-[#1a2236] border border-white/[0.07] rounded-2xl p-6 flex flex-col gap-4 shadow-2xl hover:-translate-y-1 hover:shadow-[0_32px_60px_-12px_rgba(0,0,0,0.7)] transition-all duration-300">

    <!-- Status Badge -->
    <div
      class="absolute top-5 right-5 flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold font-mono tracking-widest"
      :class="statusClasses.badge"
    >
      <span class="w-1.5 h-1.5 rounded-full" :class="statusClasses.dot" />
      {{ node.status }}
    </div>

    <!-- Icon -->
    <div class="w-13 h-13 bg-[#111827] border border-white/[0.07] rounded-xl flex items-center justify-center text-sky-400">
      <div class="w-5">
        <IconDevice />
      </div>
    </div>

    <!-- Node Info -->
    <div class="flex flex-col gap-1">
      <h2 class="text-xl font-bold font-mono text-slate-100 tracking-tight">{{ node.name }}</h2>
    </div>

    <!-- Divider -->
    <div class="h-px bg-white/[0.07]" />

    <!-- Actions -->
    <div class="flex items-center gap-2.5">
      <button
        :disabled="node.status === 'FREE'"
        @click="emit('release', props.device)"
        class="flex-1 py-2.5 bg-sky-400/10 border border-sky-400/25 rounded-xl text-sky-400 text-sm font-semibold text-center hover:bg-sky-400/20 hover:border-sky-400/50 transition-all duration-200"
        :class="{ 'cursor-not-allowed! opacity-35': node.status === 'FREE' }"
        >
        Release
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Device } from '@/utils/types'
import IconDevice from '../shared/icons/IconDevice.vue'

interface Node {
  id: string | number
  name: string
  status: 'ASSIGNED' | 'FREE'
}

const props = withDefaults(defineProps<{ node: Node, device: Device }>(), {
  node: () => ({
    id: 842,
    name: 'Node #842',
    status: 'FREE',
  }),
})

const emit = defineEmits<{
  (e: 'release', device: Device): void
}>()

const statusClasses = computed(() => {
  const map: Record<Node['status'], { badge: string; dot: string }> = {
    ASSIGNED: {
      badge: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
      dot:   'bg-emerald-400 shadow-[0_0_6px_#4ade80] animate-pulse',
    },
    FREE: {
      badge: 'bg-amber-400/10 text-amber-400 border border-amber-400/25',
      dot:   'bg-amber-400',
    }
  }
  return map[props.node.status] ?? map.FREE
})

</script>
