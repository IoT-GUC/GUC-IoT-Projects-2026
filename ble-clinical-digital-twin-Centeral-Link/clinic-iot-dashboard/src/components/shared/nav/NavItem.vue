<script setup lang="ts">
defineProps({
    text: {
        type: String,
        required: true
    },
    icon: {
        type: Object,
        required: true
    },
    to: {
        type: String,
        required: true
    }
})
</script>

<template>
    <RouterLink :to="{name: to}" class="rounded-lg text-[#94A3B8]" active-class="text-white bg-[#259DF4]">
        <div class="px-3 py-2 flex gap-3 w-full items-center">
            <div class="w-5">
                <component :is="icon"></component>
            </div>
            <div>
                <p class="text-[16px]">
                    {{ text }}
                </p>
            </div>
        </div>
    </RouterLink>
</template>