<script setup lang="ts">
import { computed, ref } from 'vue';
import type { DeviceWithRouterInfo } from '../../utils/types';
import IconOptions from '../shared/icons/IconOptions.vue';
const ACTIVE_TIMEOUT = Number(import.meta.env.VITE_ACTIVE_TIMEOUT) || 60;
const IDLE_TIMEOUT = Number(import.meta.env.VITE_IDLE_TIMEOUT) || 120;
const GROUP_SIZE = 10;


const props = defineProps<{
  items: DeviceWithRouterInfo[]
}>();

const emit = defineEmits(['view', 'release']);

const activeMenu = ref<string | null>(null);

const toggleMenu = (id: string) => {
  activeMenu.value = activeMenu.value === id ? null : id;
};

// Helper to get initials for the avatar
const getInitials = (name: string) => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
};

// Logic to determine status color based on some data (mocked for visual fidelity)
const getStatusClasses = (status: string) => {
  if (status == 'Active') return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
  if (status == 'Idle') return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
};

const patientsStatus = computed(() => {
  const status = {} as Record<string, string>;
  props.items.forEach(item => {
    const timeDiff = new Date().getTime() - new Date(item.last_record_timestamp).getTime();
    const seconds = Math.floor(timeDiff / 1000);
    if (seconds < ACTIVE_TIMEOUT) {
      status[item.id] = 'Active';
    } else if (seconds < IDLE_TIMEOUT) {
      status[item.id] = 'Idle';
    } else {
      status[item.id] = 'Offline';
    }
  });
  return status;
})

function formatTimeDiff(timestamp: string) {
  const timeDiff = new Date().getTime() - new Date(timestamp).getTime();
  const seconds = Math.floor(timeDiff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

const group = ref(0);
const groupDevices = computed(() => props.items.slice(group.value * GROUP_SIZE, group.value * GROUP_SIZE + GROUP_SIZE))
const groupsCount = computed(() => Math.ceil(props.items.length / GROUP_SIZE))

const setGroup = (n: number) => {
  group.value = n;
}

const nextGroup = () => {
  if (group.value < groupsCount.value - 1) setGroup(group.value + 1);
}

const prevGroup = () => {
  if (group.value > 0) setGroup(group.value - 1);
}

</script>

<template>
  <div class="w-full bg-[#0b1120] text-slate-300 rounded-lg overflow-hidden border border-slate-800/50">
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800/60 bg-[#0f172a]/50">
            <th class="px-6 py-4 font-semibold">User Profile</th>
            <th class="px-6 py-4 font-semibold">Current Location</th>
            <th class="px-6 py-4 font-semibold">Connected Device</th>
            <th class="px-6 py-4 font-semibold">Duration</th>
            <th class="px-6 py-4 font-semibold">Status</th>
            <th class="px-6 py-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/40">
          <tr v-for="item in groupDevices" :key="item.id" class="hover:bg-slate-800/20 transition-colors group">
            <td class="px-6 py-5">
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                  <span class="text-xs font-bold text-sky-400">{{ getInitials(item.holder_name) }}</span>
                </div>
                <div class="flex flex-col">
                  <span class="text-[15px] font-semibold text-white leading-tight">{{ item.holder_name }}</span>
                </div>
              </div>
            </td>

            <td class="px-6 py-5">
              <div class="flex items-center gap-2 text-sm text-slate-200">
                <MapPin :size="16" class="text-slate-500" />
                {{ item.router_name }}
              </div>
            </td>

            <td class="px-6 py-5">
              <div class="flex items-center gap-3">
                <Router v-if="item.name.includes('GW')" :size="18" class="text-sky-500" />
                <Smartphone v-else :size="18" class="text-sky-500" />
                <div class="flex flex-col text-sm">
                  <span class="text-slate-200 font-medium">{{ item.name }}</span>
                </div>
              </div>
            </td>

            <td class="px-6 py-5">
              <span class="text-sm font-medium text-slate-300">{{ formatTimeDiff(item.last_record_timestamp) }}</span>
            </td>

            <td class="px-6 py-5">
              <div
                :class="['inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-bold tracking-wide capitalize', getStatusClasses(patientsStatus[item.id] || 'Offline')]">
                <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                {{ patientsStatus[item.id] }}
              </div>
            </td>

            <td class="px-6 py-5 text-right relative">
              <button @click="toggleMenu(item.id)"
                class="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-slate-500 group-hover:text-slate-300">
                <IconOptions />
              </button>

              <div v-if="activeMenu === item.id"
                class="absolute right-6 top-14 w-32 bg-[#1e293b] border border-slate-700 rounded-lg shadow-xl z-10 py-1">
                <button @click="emit('view', item); activeMenu = null"
                  class="w-full text-left px-4 py-2 text-xs hover:bg-slate-700 text-slate-200">View Details</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="px-6 py-4 flex justify-between items-center bg-[#0b1120] border-t border-slate-800/60">
      <span class="text-xs text-slate-500">Showing {{ items.length }} of 12,842 active sessions</span>
      <div class="flex gap-2">
        <button class="px-4 py-1.5 text-xs font-bold rounded-md hover:bg-slate-700 transition-colors"
          :class="[group > 0 ? 'bg-slate-800 text-white' : 'text-slate-500']" @click="prevGroup">Previous</button>
        <button
          class="px-4 py-1.5 text-xs font-bold  rounded-md hover:bg-slate-700"
          :class="[group < groupsCount - 1? 'bg-slate-800 text-white' : 'text-slate-500']"
          @click="nextGroup">Next</button>
      </div>
    </div>
  </div>
</template>