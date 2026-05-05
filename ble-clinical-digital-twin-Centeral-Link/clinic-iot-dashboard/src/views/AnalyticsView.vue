<script setup lang="ts">
import { onMounted } from 'vue';
import MainLayout from '../components/shared/layout/MainLayout.vue';
import PlaceHolder from '../components/shared/layout/PlaceHolder.vue';
import { useHourlyPatients, useHourlyRecords, useHourlySessionsDuration } from '@/utils/hooks/records';
import HourlyPatientsChart from '@/components/analytics/HourlyPatientsChart.vue';
import { useRoutersMap } from '@/utils/hooks/routers';
import RoutersMap from '@/components/analytics/RoutersMap.vue';
import HourlyRecordsChart from '@/components/analytics/HourlyRecordsChart.vue';
import HourlySessionDurationChart from '@/components/analytics/HourlySessionDurationChart.vue';

const { records: hourlyPatients, loading: hourlyPatientsLoading, fetchHourlyPatients } = useHourlyPatients();
const { records: hourlyRecords, loading: hourlyRecordsLoading, fetchHourlyRecords } = useHourlyRecords();
const { sessions: hourlySessionsDuration, loading: hourlySessionsDurationLoading, fetchHourlySessionsDuration } = useHourlySessionsDuration();
const { routersMap, loading: routersMapLoading, fetchRoutersMap } = useRoutersMap();

console.log(hourlyRecords, hourlySessionsDuration)

onMounted(() => {
    fetchHourlyPatients();
    fetchHourlyRecords();
    fetchHourlySessionsDuration();
    fetchRoutersMap();
});

</script>

<template>
    <MainLayout>
        <div class="p-8 flex flex-col gap-8 items-stretch">
            <PlaceHolder v-if="routersMapLoading" class="h-180" />
            <RoutersMap v-if="routersMap" :entries="routersMap!" />

            <PlaceHolder v-if="hourlyPatientsLoading || hourlyRecordsLoading || hourlySessionsDurationLoading"
                class="h-180" />
            <HourlyPatientsChart v-if="hourlyPatients" :data="hourlyPatients!" />
            <HourlyRecordsChart v-if="hourlyRecords" :data="hourlyRecords!" />
            <HourlySessionDurationChart v-if="hourlySessionsDuration" :data="hourlySessionsDuration!" />
        </div>
    </MainLayout>
</template>