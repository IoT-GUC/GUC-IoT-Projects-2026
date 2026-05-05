<script setup lang="ts">
import { computed, ref } from 'vue';
import type { DeviceWithRouterInfo } from '../../utils/types';
import IconChevron from '../shared/icons/IconChevron.vue';
const ACTIVE_TIMEOUT = Number(import.meta.env.VITE_ACTIVE_TIMEOUT) || 60;
const IDLE_TIMEOUT = Number(import.meta.env.VITE_IDLE_TIMEOUT) || 120;
const GROUP_SIZE = 3;


const props = defineProps<{
  devices: DeviceWithRouterInfo[]
}>();

const group = ref(0);
const groupDevices = computed(() => props.devices.slice(group.value * GROUP_SIZE, group.value * GROUP_SIZE + GROUP_SIZE))
const groupsCount = computed(() => Math.ceil(props.devices.length / GROUP_SIZE))

const setGroup = (n: number) => {
  group.value = n;
}

const nextGroup = () => {
  if (group.value < groupsCount.value - 1) setGroup(group.value + 1);
}

const prevGroup = () => {
  if (group.value > 0) setGroup(group.value - 1);
}

// Helper to generate initials or placeholder colors based on name
const getAvatarColor = (name: string) => {
  const colors = ['bg-orange-200', 'bg-beige-100', 'bg-slate-100', 'bg-gray-300'];
  const index = name.length % colors.length;
  return colors[index];
};

// Mock status logic (since not in interface, defaulting to active/idle)
const getStatus = (timestamp: string) => {
  const timeDiff = new Date().getTime() - new Date(timestamp).getTime();
  const seconds = Math.floor(timeDiff / (1000));
  if (seconds > IDLE_TIMEOUT) return { label: 'Offline', class: 'text-rose-400 bg-rose-400/10 border-rose-400/20' };
  if (seconds > ACTIVE_TIMEOUT) return { label: 'Idle', class: 'text-orange-400 bg-orange-400/10 border-orange-400/20' };
  return { label: 'Active', class: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' };
};
</script>

<template>
  <div class="w-full bg-[#111827] text-slate-300 p-6 rounded-xl font-sans border border-slate-800">
    <div class="flex justify-between items-start mb-8">
      <div>
        <h2 class="text-xl font-semibold text-white">Tracked Active Users</h2>
        <!-- <p class="text-sm text-slate-500">Real-time geolocation and device health</p> -->
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
            <th class="pb-4 font-semibold">User Details</th>
            <th class="pb-4 font-semibold text-center">Status</th>
            <th class="pb-4 font-semibold">Device Info</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/50">
          <tr v-for="device in groupDevices" :key="device.id" class="group hover:bg-slate-800/30 transition-colors">
            <td class="py-4">
              <div class="flex items-center gap-3">
                <div :class="['w-10 h-10 rounded-full shrink-0', getAvatarColor(device.holder_name)]"></div>
                <div class="flex flex-col">
                  <span class="text-sm font-medium text-white">{{ device.holder_name }}</span>
                  <span class="text-xs text-slate-500">{{ device.id }}</span>
                </div>
              </div>
            </td>

            <td class="py-4 text-center">
              <span
                :class="['px-2.5 py-0.5 rounded-full text-[10px] font-bold border flex items-center justify-center w-fit mx-auto gap-1.5', getStatus(device.last_record_timestamp).class]">
                <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                {{ getStatus(device.last_record_timestamp).label }}
              </span>
            </td>

            <td class="py-4">
              <div class="flex flex-col">
                <span class="text-sm text-slate-300">{{ device.name }}</span>
              </div>
            </td>

          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-8 pt-4 border-t border-slate-800">
      <p class="text-xs text-slate-500">
        Showing {{ groupDevices.length }} of {{ devices.length }}
      </p>
      <div class="flex items-center gap-1">
        <button class="w-8 h-8 flex items-center justify-center rounded text-white text-xs font-bold hover:bg-gray-500" @click="prevGroup">
          <IconChevron class="w-4" />
        </button>
        <button v-for="i in groupsCount" :key="i"
          class="w-8 h-8 flex items-center justify-center rounded text-white text-xs font-bold"
          :class="{ 'bg-sky-500': group == i - 1, ' hover:bg-gray-500': group != i - 1}" @click="setGroup(i-1)">
          {{ i }}
        </button>
        <button class="w-8 h-8 flex items-center justify-center rounded text-white text-xs font-bold -scale-x-100 hover:bg-gray-500" @click="nextGroup">
          <IconChevron class="w-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for table if needed */
.overflow-x-auto::-webkit-scrollbar {
  height: 4px;
}

.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 10px;
}
</style>