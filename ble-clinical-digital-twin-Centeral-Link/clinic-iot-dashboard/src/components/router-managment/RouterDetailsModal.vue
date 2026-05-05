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
          class="relative w-full max-w-4xl bg-[#0f1117] border border-white/10 rounded-2xl shadow-2xl shadow-black/60 scale-90 overflow-y-scroll max-h-5/6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
          @click.stop
        >
          <!-- Top accent line -->
          <div class="h-px w-full bg-linear-to-r from-transparent via-blue-500/60 to-transparent" />

          <div class="flex flex-col items-center gap-8">
            <SingleHeader :icon="IconRouter" :title="props.router.name" :status="status" :statusColor="statusColor" :feature="{name: 'CONNECTED DEVICES', value: devices?.length ?? ''}"/>
            <PlaceHolder v-if="hourlySessions == undefined" class="h-24" />
            <RouterHourlySessionsChart v-if="hourlySessions != undefined" :data="hourlySessions ?? []" class="w-9/12" />
            <PlaceHolder v-if="devices == undefined" />
            <PatientsTable v-if="hourlySessions != undefined" :devices="devices ?? []"/>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouterDevices, useRouterHourlySessions } from '../../utils/hooks/routers'
import type { Router } from '../../utils/types';
import PatientsTable from './PatientsTable.vue';
import SingleHeader from '../shared/SingleHeader.vue';
import IconRouter from '../shared/icons/IconRouter.vue';
import RouterHourlySessionsChart from './RouterHourlySessionsChart.vue';
import PlaceHolder from '../shared/layout/PlaceHolder.vue';

const props = defineProps<{
  modelValue: boolean,
  router: Router
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()


const { devices, loading: devicesLoading, error: devicesError, fetchRouterDevices } = useRouterDevices(props.router.id);
const { hourlySessions, loading: hourlySessionsLoading, error: hourlySessionsError, fetchRouterHourlySessions } = useRouterHourlySessions(props.router.id);

const status = computed(() => devices.value ? (devices.value.length  > 0 ? 'Active': 'Offline') : '')
const statusColor = computed(() => devices.value ? (devices.value.length  > 0 ? 'green': 'red') : 'transparent')

function handleClose() {
  emit('update:modelValue', false)
}


onMounted(() => {
  fetchRouterDevices();
  fetchRouterHourlySessions();
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
