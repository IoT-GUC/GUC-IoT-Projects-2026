<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="handleClose">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="handleClose" />

        <!-- Modal panel -->
        <div
          class="relative w-full max-w-4xl bg-[#0f1117] border border-white/10 rounded-2xl shadow-2xl shadow-black/60 scale-90 overflow-y-scroll max-h-5/6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
          @click.stop>
          <!-- Top accent line -->
          <div class="h-px w-full bg-linear-to-r from-transparent via-blue-500/60 to-transparent" />

          <div class="flex flex-col items-center gap-8 pb-8">
            <SingleHeader :icon="IconUserTracking" :title="props.patient.holder_name" :status="status"
              :statusColor="statusColor" :feature="{ name: 'SESSIONS COUNT', value: sessions?.length ?? '' }" />
            <div v-if="sessions == undefined" class="p-8 w-full">
              <PlaceHolder class="h-56" />
            </div>
            <PatientSessionsChart v-if="sessions != undefined" :data="sessions ?? []" class="w-9/12" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import type { DeviceWithRouterInfo } from '../../utils/types';
import SingleHeader from '../shared/SingleHeader.vue';
import PlaceHolder from '../shared/layout/PlaceHolder.vue';
import { usePatientSessions } from '@/utils/hooks/patients';
import IconUserTracking from '../shared/icons/IconUserTracking.vue';
import PatientSessionsChart from './PatientSessionsChart.vue';
const ACTIVE_TIMEOUT = Number(import.meta.env.VITE_ACTIVE_TIMEOUT) || 60;
const IDLE_TIMEOUT = Number(import.meta.env.VITE_IDLE_TIMEOUT) || 120;

export type PatientDetails = DeviceWithRouterInfo & { patient_id: string }

const props = defineProps<{
  modelValue: boolean,
  patient: PatientDetails
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const status = computed(() => {
  const timeDiff = new Date().getTime() - new Date(props.patient.last_record_timestamp).getTime();
  const seconds = Math.floor(timeDiff / 1000);
  if (seconds < ACTIVE_TIMEOUT) return 'Active';
  if (seconds < IDLE_TIMEOUT) return 'Idle';
  return 'Offline';
})

const statusColor = computed(() => status.value == 'Active' ? 'green' : status.value == 'Idle' ? 'orange' : 'red');

const { sessions, loading: sessionsLoading, error: sessionsError, fetchPatientSessions } = usePatientSessions(props.patient.patient_id);

function handleClose() {
  emit('update:modelValue', false)
}


onMounted(() => {
  if (props.patient.patient_id) {
    fetchPatientSessions()
  }
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
