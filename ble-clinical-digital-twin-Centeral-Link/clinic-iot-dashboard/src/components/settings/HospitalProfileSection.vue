<script setup lang="ts">
const props = defineProps<{
  hospitalName: string
  facilityId: string
  address: string
}>()

</script>

<template>
  <section>
    <h2 class="text-white font-bold text-lg mb-1">Hospital Profile</h2>
    <p class="text-gray-400 text-sm mb-4">Global settings for your medical facility identification.</p>

    <div class="bg-[#1a1f2e] border border-gray-700 rounded-xl p-6 space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Hospital Name -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Hospital Name</label>
          <input
            type="text"
            :value="hospitalName"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <!-- Facility ID (read-only) -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Facility ID</label>
          <input
            type="text"
            :value="facilityId"
            disabled
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-gray-500 text-sm cursor-not-allowed"
          />
        </div>
      </div>

      <!-- Address -->
      <div class="flex flex-col gap-1">
        <label class="text-gray-300 text-sm">Primary Address</label>
        <input
          type="text"
          :value="address"
          class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors w-full"
        />
      </div>
    </div>
  </section>
</template>
