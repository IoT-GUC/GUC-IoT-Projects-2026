<script setup lang="ts">

defineProps({
    text: {
        type: String,
        required: true
    }
})

</script>

<template>
    <div class="flex gap-3 items-center">
        <div class="w-5.5 text-[#259DF4]">
            <slot />
        </div>
        <p class="text-[16px] text-[#CBD5E1]">
            {{ text }}
        </p>
    </div>
</template>