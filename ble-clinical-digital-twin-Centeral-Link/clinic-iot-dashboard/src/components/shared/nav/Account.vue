<script setup lang="ts">
const hospitalId = localStorage.getItem('hospitalId')
</script>

<template>
    <div class="p-4 flex gap-3 items-center border-t border-[#1E293B]">
        <div class="rounded-full overflow-hidden">
            <img width="32" height="32" src="/user-avatar.png" />
        </div>
        <div class="flex flex-col">
            <div>
                <p class="font-medium text-white text-sm">{{ hospitalId }}</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">System Admin</p>
            </div>
        </div>
    </div>
</template>