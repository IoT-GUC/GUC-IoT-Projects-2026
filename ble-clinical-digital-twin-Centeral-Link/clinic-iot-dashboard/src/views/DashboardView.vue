<script setup lang="ts">
import DashboardHeader from '../components/dashboard/DashboardHeader.vue';
import MainLayout from '../components/shared/layout/MainLayout.vue';
import Card from '../components/dashboard/Card.vue';
import IconRouter from '../components/shared/icons/IconRouter.vue';
import IconDevice from '../components/shared/icons/IconDevice.vue';
import BlueprintView from '../components/dashboard/BlueprintView.vue';
import { useRoutersMap } from '../utils/hooks/routers';
import { computed, onMounted, onUnmounted } from 'vue';
import PlaceHolder from '../components/shared/layout/PlaceHolder.vue';
const REALTIME_PERIOD = Number(import.meta.env.REALTIME_PERIOD || 60);

const { routersMap, loading, error, fetchRoutersMap, fetchRoutersMapSilently } = useRoutersMap()

const routersCount = computed(() => routersMap.value?.length)
const devicesCount = computed(() => routersMap.value ?
    routersMap.value.reduce((acc, curr) => acc + curr.connected_devices_count, 0)
    : undefined)

let interval: number | undefined= undefined

onMounted(() => {
    fetchRoutersMap()
    interval = setInterval(() => {
        fetchRoutersMapSilently()
        console.log('fetchRoutersMap')
    }, REALTIME_PERIOD * 1000)
})

onUnmounted(() => {
    if (interval) {
        clearInterval(interval)
    }
})

</script>

<template>
    <MainLayout>
        <DashboardHeader />
        <div class="p-8 flex flex-col gap-8 items-stretch">
            <PlaceHolder v-if="loading" class="h-32" />
            <div class="flex gap-6" v-else>
                <Card title="Routers Count" :icon="IconRouter" :text="routersCount" icon-color="#259DF4"
                    icon-bg="#259DF416" />
                <Card title="Patients Count" :icon="IconDevice" :text="devicesCount" icon-color="#10B981"
                    icon-bg="#10B98116" />
            </div>
            <PlaceHolder v-if="loading" class="h-100" />
            <div v-else>
                <BlueprintView :routers-map="routersMap" />
            </div>
        </div>
    </MainLayout>
</template>