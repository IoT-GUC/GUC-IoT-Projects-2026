<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import Header from '../components/shared/Header.vue';
import MainLayout from '../components/shared/layout/MainLayout.vue';
import PlaceHolder from '../components/shared/layout/PlaceHolder.vue';
import AddPatientModal from '../components/patient-tracking/AddPatientModal.vue';
import { useNotifications } from '../utils/hooks/notifications';
import type { DeviceWithRouterInfo, Patient } from '@/utils/types';
import PatientsTable from '@/components/patient-tracking/PatientsTable.vue';
import { useDevicesPatients, useDevicesWithRouterInfo } from '@/utils/hooks/devices';
import PatientDetailsModal, { type PatientDetails } from '@/components/patient-tracking/PatientDetailsModal.vue';

const { devices, loading, fetchDevicesWithRouterInfo } = useDevicesWithRouterInfo();
const { devicesPatients, loading: devicesPatientsLoading, error: devicesPatientsError, fetchDevicesPatients } = useDevicesPatients();

const searchQuery = ref('');

const filteredPatients = computed(() => {
    let res = devices.value;
    if (searchQuery.value)
        res = devices.value?.filter(device => device.holder_name.toLowerCase().includes(searchQuery.value.toLowerCase()));
    return res
});

const modalVisible = ref(false);

const { success } = useNotifications();

function addNewPatient(){
    modalVisible.value = true;
}

function closeModal(){
    modalVisible.value = false;
}

const selectedPatient = ref<PatientDetails|null>(null);

function openPatientDetails(patient: DeviceWithRouterInfo){
    selectedPatient.value = {...patient, patient_id: devicesPatients.value?.[patient.id] ?? ''};
}

function closePatientDetails(){
    selectedPatient.value = null;
}

function addNewPatientSuccess(){
    modalVisible.value = false;
    success('Patient added successfully');
    fetchDevicesWithRouterInfo();
    fetchDevicesPatients();
}

onMounted(() => {
    fetchDevicesWithRouterInfo();
    fetchDevicesPatients();
});

</script>

<template>
    <MainLayout>
        <Header v-model="searchQuery" search-placeholder="Search Patients ..." add-new-text="Add Patient" @add-new="addNewPatient" />
        <div class="p-8 flex flex-col gap-8 items-stretch">
            <div class="flex gap-6 justify-between items-center">
                <div class="flex flex-col g-2">
                    <p class="font-black text-3xl text-white">Patient Managment</p>
                    <p class="text-base text-gray-500">Monitor and control your connected IoT infrastructure in real
                        time</p>
                </div>
                <div class="py-2 px-4 rounded-2xl bg-[#1E293B80] border border-[#1E293B]">
                    <p class="text-xs text-gray-500 font-bold">TOTAL ONLINE</p>
                    <p class="text-xl font-bold text-[#259DF4]">{{ devices?.length }}</p>
                </div>
            </div>
            <PlaceHolder v-if="loading || devicesPatientsLoading" class="h-120" />
            <div>
                <PatientsTable :items="filteredPatients || []" @view="openPatientDetails"  />
            </div>
        </div>
    </MainLayout>
    <AddPatientModal :model-value="modalVisible" @update:model-value="closeModal" @success="addNewPatientSuccess" />
    <PatientDetailsModal v-if="selectedPatient !== null" :model-value="selectedPatient !== null" :patient="selectedPatient!" @update:model-value="closePatientDetails" />
</template>