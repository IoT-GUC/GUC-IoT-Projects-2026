import { computed, ref } from 'vue'
import { getData, postData, putData } from '../api/http'
import type { Device, DeviceWithRouterInfo, CreateDevicePayload } from '../types'

export function useDevices() {
  const devices = ref<Device[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchDevices(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ devices: Device[] }>('/devices')
      devices.value = response.devices
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDevice(payload: CreateDevicePayload): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await postData<void>('/devices', payload)
      await fetchDevices()
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { devices, loading, error, fetchDevices, createDevice }
}

export function useDevicesWithRouterInfo() {
  const devices = ref<DeviceWithRouterInfo[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchDevicesWithRouterInfo(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ devices: DeviceWithRouterInfo[] }>(
        '/devices/with-routers-info',
      )
      devices.value = response.devices
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { devices, loading, error, fetchDevicesWithRouterInfo }
}

export function useDevicesPatients() {
  const { devices, loading, error, fetchDevices } = useDevices()
  const devicesPatients = computed(() => {
    if (!devices.value) return undefined
    const patients = {} as Record<string, string | null>
    devices.value?.forEach(d => patients[d.id] = d.patient_id)
    return patients
  })

  return { devicesPatients, loading, error, fetchDevicesPatients: fetchDevices }
}

export function useReleaseDevice() {
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function releaseDevice(id: string): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await putData<void>(`/devices/${id}/release`, {})
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { loading, error, releaseDevice }
}
