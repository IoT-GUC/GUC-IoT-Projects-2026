<script setup lang="ts">
import { ref } from 'vue'

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const localError = ref<string | undefined>(undefined)

const emit = defineEmits<{
  (e: 'password-change', payload: { currentPassword: string; newPassword: string }): void
}>()


defineExpose({ currentPassword, newPassword, confirmPassword })
</script>

<template>
  <section>
    <h2 class="text-white font-bold text-lg mb-1">Password Reset</h2>
    <p class="text-gray-400 text-sm mb-4">Ensure your account security by updating your password periodically.</p>

    <div class="bg-[#1a1f2e] border border-gray-700 rounded-xl p-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Current Password -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Current Password</label>
          <input
            v-model="currentPassword"
            type="password"
            placeholder="••••••••"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors placeholder-gray-600"
          />
        </div>

        <!-- New Password -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">New Password</label>
          <input
            v-model="newPassword"
            type="password"
            placeholder="••••••••"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors placeholder-gray-600"
          />
        </div>

        <!-- Confirm New Password -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Confirm New Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="••••••••"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors placeholder-gray-600"
          />
        </div>
      </div>

      <p v-if="localError" class="text-red-400 text-xs mt-3">{{ localError }}</p>
    </div>
  </section>
</template>
