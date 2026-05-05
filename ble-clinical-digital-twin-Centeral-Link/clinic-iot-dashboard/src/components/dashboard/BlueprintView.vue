<script setup lang="ts">
import IconBlueprint from '../shared/icons/IconBlueprint.vue';
import IconFit from '../shared/icons/IconFit.vue';
import IconMinus from '../shared/icons/IconMinus.vue';
import IconPlus from '../shared/icons/IconPlus.vue';
import Blueprint from '../shared/Blueprint.vue';
import { ref, type PropType } from 'vue';
import type { RouterMapEntry } from '../../utils/types';

defineProps({
    routersMap: {
        type: Array as PropType<RouterMapEntry[]>,
        default: () => []
    }
})

const scale = ref(1);

function scaleUp() {
    if (scale.value >= 2) return;
    scale.value += 0.1;
}
function scaleDown() {
    if (scale.value <= 0.5) return;
    scale.value -= 0.1;
}

function scaleFit() {
    scale.value = 1;
}

</script>

<template>
    <div class="w-full rounded-xl bg-[#0F172A70] border border-[#1E293B]">
        <div class="flex p-4 bg-[#1E293B32] border-b border-[#1E293B] gap-2 items-center">
            <div class="w-4 text-[#259DF4]">
                <IconBlueprint />
            </div>
            <div class="grow">
                <p class="font-bold text-white text-base">
                    Clinic Floor Plan
                </p>
            </div>
            <div @click="scaleUp"
                class="w-7 h-7 flex items-center justify-center rounded bg-[#1E293B] border border-[#334155]">
                <div class="text-white w-3.5">
                    <IconPlus />
                </div>
            </div>
            <div @click="scaleDown"
                class="w-7 h-7 flex items-center justify-center rounded bg-[#1E293B] border border-[#334155]">
                <div class="text-white w-3.5">
                    <IconMinus />
                </div>
            </div>
            <div @click="scaleFit"
                class="w-7 h-7 flex items-center justify-center rounded bg-[#1E293B] border border-[#334155]">
                <div class="text-white w-3.5">
                    <IconFit />
                </div>
            </div>
        </div>
        <div class="pt-3 pl-3 bg-[#11202F]">
            <div class="p-12 bg-[#101925]">
                <div class="overflow-hidden max-w-full rounded-lg">
                    <Blueprint :style="{ scale: scale }" :items="routersMap" />
                </div>
            </div>
        </div>
    </div>
</template>
