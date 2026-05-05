<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="handleClose"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="handleClose" />

        <!-- Modal panel -->
        <div
          class="relative w-full max-w-lg bg-[#0f1117] border border-white/10 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden"
          @click.stop
        >
          <!-- Top accent line -->
          <div class="h-px w-full bg-linear-to-r from-transparent via-blue-500/60 to-transparent" />

          <div class="p-7 flex flex-col gap-4">
            <!-- Header -->
            <div class="flex items-start justify-between mb-7">
              <div>
                <h2 class="text-2xl font-bold text-white tracking-tight">Add User</h2>
                <p class="text-sm text-white/40 mt-1">Add New User for the AI monitoring suite</p>
              </div>
              <button
                class="w-8 h-8 flex items-center justify-center rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all duration-150"
                @click="handleClose"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <!-- Form -->
            <div class="space-y-5 flex flex-col gap-4">
              <!-- User Name -->
              <div>
                <label class="block text-xs font-semibold text-white/50 tracking-widest uppercase mb-2">
                  User Name
                </label>
                <input
                  v-model="form.name"
                  type="text"
                  placeholder="User Name"
                  :disabled="loading"
                  class="w-full px-4 py-3 bg-[#1a1f2e] border rounded-lg text-white placeholder-white/20 text-sm outline-none transition-all duration-150 focus:ring-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  :class="errors.name
                    ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30'
                    : 'border-white/10 focus:border-blue-500/60 focus:ring-blue-500/20'"
                />
                <p v-if="errors.name" class="mt-1.5 text-xs text-red-400">{{ errors.name }}</p>
              </div>

              <!-- Device ID -->
              <div>
                <label class="block text-xs font-semibold text-white/50 tracking-widest uppercase mb-2">
                  User ID
                </label>
                <div class="relative">
                  <select
                    v-model="form.device_id"
                    :disabled="loading"
                    class="w-full px-4 py-3 bg-[#1a1f2e] border rounded-lg text-white placeholder-white/20 text-sm outline-none transition-all duration-150 focus:ring-1 pr-24 font-mono disabled:opacity-50 disabled:cursor-not-allowed"
                    :class="errors.device_id
                      ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30'
                      : 'border-white/10 focus:border-blue-500/60 focus:ring-blue-500/20'"
                  >
                    <option disabled selected>Device Name</option>
                    <option
                      v-for="device in freeDevices"
                      :key="device.id"
                      :value="device.id"
                    >
                      {{ device.name }}
                    </option>
                </select>
                </div>
                <p v-if="errors.device_id" class="mt-1.5 text-xs text-red-400">{{ errors.device_id }}</p>
              </div>
            </div>

            <!-- API error banner -->
            <Transition name="fade">
              <div
                v-if="error"
                class="mt-5 flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-red-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <p class="text-xs text-red-400">{{ error }}</p>
              </div>
            </Transition>

            <!-- Submit -->
            <button
              class="mt-6 w-full py-3.5 rounded-xl font-semibold text-sm tracking-wide transition-all duration-200"
              :class="loading
                ? 'bg-blue-600/50 text-white/50 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white active:scale-[0.98]'"
              :disabled="loading"
              @click="handleSubmit"
            >
              <span v-if="!loading">Add User</span>
              <span v-else class="flex items-center justify-center gap-2">
                <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Adding User…
              </span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { usePatients } from '../../utils/hooks/patients'
import { useDevices } from '../../utils/hooks/devices';

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const { loading, error, createPatient } = usePatients()
const { loading: loadingDevices, error: errorDevices, devices, fetchDevices } = useDevices()

const freeDevices = computed(() => devices.value?.filter(device => !device.patient_id))

interface FormState {
  name: string
  device_id: string
}

interface FormErrors {
  name?: string
  device_id?: string
}

const form = reactive<FormState>({ name: '', device_id: '' })
const errors = reactive<FormErrors>({})

function resetForm() {
  form.name = ''
  form.device_id = ''
  delete errors.name
  delete errors.device_id
}

function handleClose() {
  if (loading.value) return
  resetForm()
  emit('update:modelValue', false)
}

function generateUUID() {
  form.device_id = crypto.randomUUID()
}

function validate(): boolean {
  delete errors.name
  delete errors.device_id
  let valid = true

  if (!form.name.trim()) {
    errors.name = 'User name is required.'
    valid = false
  }
  if (!form.device_id.trim()) {
    errors.device_id = 'Device ID is required.'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return

   await createPatient({
    name: form.name.trim(),
    device_id: form.device_id.trim(),
  })

  if (!error.value) {
    resetForm()
    emit('success')
    emit('update:modelValue', false)
  }
}

watch(
  () => props.modelValue,
  (open) => { if (open) resetForm() }
)

onMounted(() => {
  fetchDevices()
})

</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.25s cubic-bezier(0.34, 1.2, 0.64, 1), opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .relative {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
