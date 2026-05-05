<script setup lang="ts">
defineProps<{
  adminName: string
  adminEmail: string
}>()

</script>

<template>
  <section>
    <h2 class="text-white font-bold text-lg mb-1">Admin Information</h2>
    <p class="text-gray-400 text-sm mb-4">Update the primary contact information for system management.</p>

    <div class="bg-[#1a1f2e] border border-gray-700 rounded-xl p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Full Name -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Full Name</label>
          <input
            type="text"
            :value="adminName"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <!-- Email Address -->
        <div class="flex flex-col gap-1">
          <label class="text-gray-300 text-sm">Email Address</label>
          <input
            type="email"
            :value="adminEmail"
            class="bg-[#111827] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>
    </div>
  </section>
</template>
