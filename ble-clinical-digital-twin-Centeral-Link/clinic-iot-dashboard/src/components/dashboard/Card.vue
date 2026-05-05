<script setup lang="ts">
defineProps({
    title: {
        type: String,
        required: true
    },
    text: {
        required: true
    },
    icon: {
        type: Object,
        required: true
    },
    iconBg: {
        type: String,
        required: true
    },
    iconColor: {
        type: String,
        required: true
    }
})
</script>

<template>
    <div class="w-62.5 bg-[#0F172A70] border border-[#1E293B] rounded-xl p-5 pb-8 flex flex-col items-stretch gap-4">
        <div class="flex justify-between items-center">
            <div>
                <p class="text-sm font-medium text-gray-500">{{ title }}</p>
            </div>
            <div class="w-8 h-8 flex justify-center items-center rounded-lg" :style="{backgroundColor: iconBg}">
                <div class="w-5" :style="{color: iconColor}">
                    <component :is="icon"></component>
                </div>
            </div>
        </div>
        <div>
            <p class="text-white text-2xl font-bold">{{ text }}</p>
        </div>
        <div>
            <slot />
        </div>
    </div>
</template>