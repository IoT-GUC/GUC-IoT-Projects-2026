import { computed, ref } from 'vue'
import { getData, postData } from '../api/http'
import type {
  Router,
  RouterMapEntry,
  RouterHourlySession,
  DeviceWithRouterInfo,
  CreateRouterPayload,
} from '../types'

export function useRouters() {
  const routers = ref<Router[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchRouters(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ routers: Router[] }>('/routers')
      routers.value = response.routers
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createRouter(payload: CreateRouterPayload): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await postData<void>('/routers', payload)
      await fetchRouters()
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { routers, loading, error, fetchRouters, createRouter }
}

export function useRoutersMap() {
  const routersMap = ref<RouterMapEntry[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchRoutersMap(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ routers_map: RouterMapEntry[] }>('/routers/map')
      routersMap.value = response.routers_map
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRoutersMapSilently(): Promise<void> {
   try {
      const response = await getData<{ routers_map: RouterMapEntry[] }>('/routers/map')
      routersMap.value = response.routers_map
    } catch (err) {
    }
  }


  return { routersMap, loading, error, fetchRoutersMap, fetchRoutersMapSilently }
}

export function useRouterStatus() {
  const { routersMap, loading, error, fetchRoutersMap } = useRoutersMap()
  const routersStatus = computed(() => {
    if (!routersMap.value) return undefined
    const status = {} as Record<string, 'ACTIVE' | 'IDLE'>
    routersMap.value?.forEach(r => status[r.id] = r.connected_devices_count > 0 ? 'ACTIVE' : 'IDLE')
    return status
  })
  return { routersStatus, loading, error, fetchRoutersStatus: fetchRoutersMap }
}

export function useRouter(id: string) {
  const router = ref<Router | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchRouter(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ router: Router }>(`/routers/${id}`)
      router.value = response.router
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { router, loading, error, fetchRouter }
}

export function useRouterDevices(id: string) {
  const devices = ref<DeviceWithRouterInfo[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchRouterDevices(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ devices: DeviceWithRouterInfo[] }>(
        `/routers/${id}/devices`,
      )
      devices.value = response.devices
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { devices, loading, error, fetchRouterDevices }
}

export function useRouterHourlySessions(id: string) {
  const hourlySessions = ref<RouterHourlySession[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchRouterHourlySessions(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ hourly_sessions: RouterHourlySession[] }>(
        `/routers/${id}/hourly-sessions-duration`,
      )
      hourlySessions.value = response.hourly_sessions
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { hourlySessions, loading, error, fetchRouterHourlySessions }
}
