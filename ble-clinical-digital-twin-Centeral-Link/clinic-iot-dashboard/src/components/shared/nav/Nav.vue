<script setup lang="ts">
import NavItem from './NavItem.vue';
import IconAnalytics from '../icons/IconAnalytics.vue';
import IconDashboard from '../icons/IconDashboard.vue';
import IconRouterManagment from '../icons/IconRouterManagment.vue';
import IconSettings from '../icons/IconSettings.vue';
import IconUserTracking from '../icons/IconUserTracking.vue';
import IconLogo from '../icons/IconLogo.vue';
import Account from './Account.vue';
import IconDevice from '../icons/IconDevice.vue';

const navItems = [
    {
        text: 'Dashboard',
        icon: IconDashboard,
        to: 'dashboard'
    },
    {
        text: 'Router Managment',
        icon: IconRouterManagment,
        to: 'router-managment'
    },
    {
        text: 'Device Managment',
        icon: IconDevice,
        to: 'device-managment'
    },
    {
        text: 'Patient Tracking',
        icon: IconUserTracking,
        to: 'patient-tracking'
    },
    {
        text: 'Analytics',
        icon: IconAnalytics,
        to: 'analytics'
    },
    {
        text: 'Settings',
        icon: IconSettings,
        to: 'settings'
    }
]

function logout(){
    localStorage.removeItem('token')
    localStorage.removeItem('hospitalId')
    window.location.href = '/auth'
}

</script>

<template>
    <div class="min-w-63.75 flex flex-col items-stretch bg-[#0F172A80] border border-[#1E293B] min-h-screen">
        <div class="flex gap-3 p-6 items-center">
            <div class="w-10 h-10 flex items-center justify-center rounded-lg bg-[#259DF4]">
                <div class="w-6 text-white">
                    <IconLogo />
                </div>
            </div>
            <div>
                <p class="font-bold text-white text-[18px]">Cerntral Link</p>
                <p class="text-xs text-[#94A3B8]">IoT Managment</p>
            </div>
        </div>
        <div class="px-4 flex flex-col items-stretch grow">
            <NavItem v-for="item in navItems" v-bind="item" :key="item.to" />
        </div>
        <button @click="logout" class="text-white font-medium text-sm flex items-center gap-2 justify-center bg-[hsl(221,41%,15%)] px-4 py-2 rounded-lg h-9 m-4!">
            Logout
        </button>
        <Account />
    </div>
</template>