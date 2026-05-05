<script setup lang="ts">
import { ref } from 'vue'
import { useSettings } from '../../utils/hooks/settings'

const { loading, error, deleteAllRecords, deleteAccount } = useSettings()

const showDeleteAccountConfirm = ref(false)
const showDeleteRecordsConfirm = ref(false)

async function handleDeleteRecords() {
  if (!showDeleteRecordsConfirm.value) {
    showDeleteRecordsConfirm.value = true
    return
  }
  await deleteAllRecords()
  showDeleteRecordsConfirm.value = false
}

async function handleDeleteAccount() {
  if (!showDeleteAccountConfirm.value) {
    showDeleteAccountConfirm.value = true
    return
  }
  await deleteAccount()
}
</script>

<template>
  <section>
    <h2 class="text-red-500 font-bold text-lg mb-1">Account Management</h2>
    <p class="text-gray-400 text-sm mb-4">Irreversible actions regarding your system access.</p>

    <div class="bg-[#1a1f2e] border border-gray-700 rounded-xl divide-y divide-gray-700">
      <!-- Delete All Records -->
      <div class="flex items-center justify-between p-5 gap-4">
        <div>
          <p class="text-red-400 text-sm font-semibold">Delete All Patient Records</p>
          <p class="text-red-500/70 text-xs mt-0.5">All patient info and records will be permanently removed.</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            v-if="showDeleteRecordsConfirm"
            @click="showDeleteRecordsConfirm = false"
            class="text-gray-400 text-sm px-3 py-1.5 rounded-lg border border-gray-600 hover:border-gray-400 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleDeleteRecords"
            :disabled="loading"
            class="bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50 font-medium whitespace-nowrap"
          >
            {{ showDeleteRecordsConfirm ? 'Confirm Delete Records' : 'Delete Records' }}
          </button>
        </div>
      </div>

      <!-- Delete Account -->
      <div class="flex items-center justify-between p-5 gap-4">
        <div>
          <p class="text-red-400 text-sm font-semibold">Delete Administrator Account</p>
          <p class="text-red-500/70 text-xs mt-0.5">Once deleted, you will lose all access to the MediIoT management console.</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            v-if="showDeleteAccountConfirm"
            @click="showDeleteAccountConfirm = false"
            class="text-gray-400 text-sm px-3 py-1.5 rounded-lg border border-gray-600 hover:border-gray-400 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleDeleteAccount"
            :disabled="loading"
            class="bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50 font-medium whitespace-nowrap"
          >
            {{ showDeleteAccountConfirm ? 'Confirm Delete Account' : 'Delete Account' }}
          </button>
        </div>
      </div>
    </div>

    <p v-if="error" class="text-red-400 text-xs mt-2">{{ error }}</p>
  </section>
</template>
