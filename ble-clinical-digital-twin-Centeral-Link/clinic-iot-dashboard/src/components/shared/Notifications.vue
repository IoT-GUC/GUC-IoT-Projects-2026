<template>
  <div class="fixed top-5 right-1/2 z-9999 space-y-2.5">
    <div
      v-for="n in notifications"
      :key="n.id"
      class="min-w-55 rounded-lg px-4 py-3 text-white shadow-lg"
      :class="{
        'bg-green-600': n.type === 'success',
        'bg-red-600': n.type === 'error',
        'bg-amber-500': n.type === 'warning',
        'bg-blue-600': n.type === 'info'
      }"
    >
      {{ n.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotifications } from '../../utils/hooks/notifications';


const { notifications } = useNotifications();
</script>