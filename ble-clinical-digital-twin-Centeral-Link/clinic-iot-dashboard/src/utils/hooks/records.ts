import { ref } from 'vue'
import { getData } from '../api/http'
import type { HourlyRecord, HourlyPatient, HourlySessionDuration } from '../types'

export function useHourlyRecords() {
  const records = ref<HourlyRecord[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchHourlyRecords(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ records_hourly: HourlyRecord[] }>(
        '/records/hourly-records',
      )
      records.value = response.records_hourly
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { records, loading, error, fetchHourlyRecords }
}

export function useHourlyPatients() {
  const records = ref<HourlyPatient[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchHourlyPatients(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ records_hourly: HourlyPatient[] }>(
        '/records/hourly-patients',
      )
      records.value = response.records_hourly
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { records, loading, error, fetchHourlyPatients }
}

export function useHourlySessionsDuration() {
  const sessions = ref<HourlySessionDuration[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchHourlySessionsDuration(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ hourly_sessions: HourlySessionDuration[] }>(
        '/records/hourly-sessions-duration',
      )
      sessions.value = response.hourly_sessions
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { sessions, loading, error, fetchHourlySessionsDuration }
}
