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

const activeRouters = computed(() => routersMap.value?.length)
const activeDevices = computed(() => routersMap.value ?
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
            <div class="flex gap-6">
                <Card title="Active Routers" :icon="IconRouter" :text="activeRouters" icon-color="#259DF4"
                    icon-bg="#259DF416" />
                <Card title="Active Devices" :icon="IconDevice" :text="activeDevices" icon-color="#10B981"
                    icon-bg="#10B98116" />
            </div>
            <PlaceHolder v-if="loading" class="h-100" />
            <div>
                <BlueprintView :routers-map="routersMap" />
            </div>
        </div>
    </MainLayout>
</template>