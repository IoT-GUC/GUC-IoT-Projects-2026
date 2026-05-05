import { ref } from 'vue'
import { putData, putFile, getData, deleteData } from '../api/http'
import type { UpdateSettingsPayload, BlueprintResponse } from '../types'
import type { Settings } from '../types'

export function useSettings() {
  const settings = ref<Settings | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchSettings(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ settings: Settings }>('/settings')
      settings.value = response.settings
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }      
  }

  async function updateSettings(payload: UpdateSettingsPayload): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await putData<void>('/settings', payload)
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteAllRecords(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await deleteData<void>('/settings/records')
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteAccount(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await deleteData<void>('/settings/account')
      localStorage.removeItem('token')
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { settings, loading, error, fetchSettings, updateSettings, deleteAllRecords, deleteAccount }
}

export function useBlueprint() {
  const blueprintUrl = ref<string | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchBlueprint(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<BlueprintResponse>('/settings/blueprint')
      blueprintUrl.value = response.url
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadBlueprint(file: File): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await putFile<void>('/settings/blueprint', file, 'image')
      await fetchBlueprint()
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { blueprintUrl, loading, error, fetchBlueprint, uploadBlueprint }
}
