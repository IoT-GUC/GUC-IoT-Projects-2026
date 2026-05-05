<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import Header from '../components/shared/Header.vue';
import MainLayout from '../components/shared/layout/MainLayout.vue';
import PlaceHolder from '../components/shared/layout/PlaceHolder.vue';
import { useNotifications } from '../utils/hooks/notifications';
import { useDevices, useReleaseDevice } from '@/utils/hooks/devices';
import DeviceCard from '@/components/device-managment/DeviceCard.vue';
import AddDeviceModal from '@/components/device-managment/AddDeviceModal.vue';
import type { Device } from '@/utils/types';

const { devices, loading, fetchDevices } = useDevices();

const searchQuery = ref('');

const filteredDevice = computed(() => {
    let res = devices.value;
    if (searchQuery.value)
        res = devices.value?.filter(device => device.name.toLowerCase().includes(searchQuery.value.toLowerCase()));
    return res
});

const modalVisible = ref(false);

const notify = useNotifications();

function addNewDevice(){
    modalVisible.value = true;
}

function closeModal(){
    modalVisible.value = false;
}

function addNewDeviceSuccess(){
    modalVisible.value = false;
    notify.success('Device added successfully');
    fetchDevices();
}

const {error: releaseError, releaseDevice } = useReleaseDevice();

async function releaseAssignedDevice(device: Device){
    await releaseDevice(device.id);
    if (releaseError.value){
        notify.error(releaseError.value);
        return;
    }
    notify.success('Device released successfully');
    fetchDevices();
}



onMounted(() => {
    fetchDevices();
});

</script>

<template>
    <MainLayout>
        <Header v-model="searchQuery" search-placeholder="Search Devices ..." add-new-text="Add Device" @add-new="addNewDevice" />
        <div class="p-8 flex flex-col gap-8 items-stretch">
            <div class="flex gap-6 justify-between items-center">
                <div class="flex flex-col g-2">
                    <p class="font-black text-3xl text-white">Device Managment</p>
                    <p class="text-base text-gray-500">Monitor and control your connected IoT infrastructure in real
                        time</p>
                </div>
                <div class="py-2 px-4 rounded-2xl bg-[#1E293B80] border border-[#1E293B]">
                    <p class="text-xs text-gray-500 font-bold">TOTAL AVALAIBLE</p>
                    <p class="text-xl font-bold text-[#259DF4]">{{ devices?.length }}</p>
                </div>
            </div>

            <PlaceHolder v-if="loading" class="h-120" />
            <div>
                <div v-if="devices" class="flex gap-4 flex-wrap">
                    <DeviceCard v-for="device in filteredDevice" :key="device.id"
                        :node="{ id: device.id, name: device.name, status: device.patient_id ? 'ASSIGNED':'FREE' }"
                        :device="device"
                        @release="releaseAssignedDevice(device)" />
                </div>
            </div>
        </div>
    </MainLayout>
    <AddDeviceModal :model-value="modalVisible" @update:model-value="closeModal" @success="addNewDeviceSuccess" />
</template>