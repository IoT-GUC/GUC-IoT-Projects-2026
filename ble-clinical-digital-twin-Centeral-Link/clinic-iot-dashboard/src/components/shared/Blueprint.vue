<script setup lang="ts">
import { onMounted, type PropType } from 'vue'
import type { RouterMapEntry } from '../../utils/types'
import { useBlueprint } from '../../utils/hooks/settings';
defineProps({
    items: {
        type: Array as PropType<RouterMapEntry[]> | undefined,
        default: undefined
    }
})
const { blueprintUrl, fetchBlueprint } = useBlueprint()

onMounted(() => fetchBlueprint())

</script>

<template>
    <div class="relative">
        <img class="w-full" :src="blueprintUrl || '/blueprint.png'" />
        <div v-for="item in items" :key="item.id" class="absolute z-10"
            :style="{ top: `${item.location_x * 100}%`, left: `${item.location_y * 100}%` }">
            <div
                class="flex items-center gap-2 bg-slate-800/80 backdrop-blur-md border border-white/10 rounded-full py-1 pr-3 pl-1.5 shadow-lg shadow-black/20 hover:scale-105 transition-transform cursor-pointer">
                <div class="relative flex h-3 w-3">
                    <span
                        class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </div>

                <span class="text-white text-sm font-semibold tabular-nums">
                    {{ item.connected_devices_count }}
                </span>
            </div>
        </div>
    </div>
</template>