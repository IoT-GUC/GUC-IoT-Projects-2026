<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSettings } from '../utils/hooks/settings'
import HospitalProfileSection from '../components/settings/HospitalProfileSection.vue'
import AdminInfoSection from '../components/settings/AdminInfoSection.vue'
import BlueprintSection from '../components/settings/BlueprintSection.vue'
import PasswordResetSection from '../components/settings/PasswordResetSection.vue'
import AccountManagementSection from '../components/settings/AccountManagementSection.vue'
import MainLayout from '../components/shared/layout/MainLayout.vue'

// Composable
const { settings, loading, error, fetchSettings, updateSettings } = useSettings()

// Form state - v-model bound to child section props
const hospitalName = ref('')
const facilityId = ref('')
const address = ref('')
const adminName = ref('')
const adminEmail = ref('')

// Password section ref
const passwordSectionRef = ref<InstanceType<typeof PasswordResetSection> | null>(null)

// Save / Cancel
const saveSuccess = ref(false)

async function handleSave() {
  saveSuccess.value = false

  const payload: Record<string, string> = {
    name: hospitalName.value,
    address: address.value,
    admin_name: adminName.value,
    admin_email: adminEmail.value,
  }

  const newPw = passwordSectionRef.value?.newPassword
  if (newPw) {
    payload.password = newPw
  }

  await updateSettings(payload)
  if (!error.value) {
    saveSuccess.value = true
    setTimeout(() => (saveSuccess.value = false), 3000)
  }
}

function handleCancel() {
  // Reset to original values — in a real app you'd re-fetch or store originals
  hospitalName.value = settings.value?.name || ''
  address.value = settings.value?.address || ''
  adminName.value = settings.value?.admin_name || ''
  adminEmail.value = settings.value?.admin_email || ''
}


onMounted(() => fetchSettings().then(() => {
  hospitalName.value = settings.value?.name || ''
  address.value = settings.value?.address || ''
  adminName.value = settings.value?.admin_name || ''
  adminEmail.value = settings.value?.admin_email || ''
}))

</script>

<template>
  <MainLayout>
    <div class="min-h-screen bg-[#0d1117] text-white font-sans">
      <!-- Top Bar -->
      <header
        class="sticky top-0 z-10 bg-[#0d1117]/90 backdrop-blur border-b border-gray-800 flex items-center justify-between px-8 py-4">
        <h1 class="text-white font-bold text-xl tracking-tight">System Settings</h1>
        <button @click="handleSave" :disabled="loading"
          class="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors">
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </header>

      <!-- Success Toast -->
      <Transition name="fade">
        <div v-if="saveSuccess"
          class="fixed top-20 right-6 z-50 bg-green-600 text-white text-sm px-4 py-2.5 rounded-lg shadow-lg">
          ✓ Settings saved successfully
        </div>
      </Transition>

      <!-- Error Toast -->
      <Transition name="fade">
        <div v-if="error"
          class="fixed top-20 right-6 z-50 bg-red-600 text-white text-sm px-4 py-2.5 rounded-lg shadow-lg">
          ✗ {{ error }}
        </div>
      </Transition>

      <!-- Page Content -->
      <main class="flex flex-col gap-10 mx-auto px-6 py-10">

        <!-- Hospital Profile -->
        <HospitalProfileSection v-model:hospitalName="hospitalName" v-model:address="address"
          :facilityId="facilityId" />

        <!-- Admin Information -->
        <AdminInfoSection v-model:adminName="adminName" v-model:adminEmail="adminEmail" />

        <!-- Blueprint -->
        <BlueprintSection />

        <!-- Password Reset -->
        <PasswordResetSection ref="passwordSectionRef" />

        <!-- Account Management -->
        <AccountManagementSection />

        <!-- Divider -->
        <hr class="border-gray-800" />

        <!-- Bottom Actions -->
        <div class="flex justify-end gap-3 pb-4">
          <button @click="handleCancel"
            class="border border-gray-600 hover:border-gray-400 text-white text-sm px-5 py-2.5 rounded-lg transition-colors font-medium">
            Cancel Changes
          </button>
          <button @click="handleSave" :disabled="loading"
            class="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-colors">
            {{ loading ? 'Saving...' : 'Update System Settings' }}
          </button>
        </div>

        <!-- Footer -->
        <footer class="text-center text-gray-600 text-xs py-4">
          © 2024 MediIoT Infrastructure Solutions. All rights reserved.
        </footer>
      </main>
    </div>
  </MainLayout>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
