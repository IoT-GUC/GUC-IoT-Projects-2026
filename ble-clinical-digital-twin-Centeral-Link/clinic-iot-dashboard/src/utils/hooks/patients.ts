import { ref } from 'vue'
import { getData, postData } from '../api/http'
import type { Patient, PatientSession, CreatePatientPayload } from '../types'

export function usePatients() {
  const patients = ref<Patient[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchPatients(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ patients: Patient[] }>('/patients')
      patients.value = response.patients
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createPatient(payload: CreatePatientPayload): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      await postData<void>('/patients', payload)
      await fetchPatients()
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { patients, loading, error, fetchPatients, createPatient }
}

export function usePatientSessions(id: string) {
  const sessions = ref<PatientSession[] | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function fetchPatientSessions(): Promise<void> {
    loading.value = true
    error.value = undefined
    try {
      const response = await getData<{ patient_sessions: PatientSession[] }>(
        `/patients/${id}/sessions`,
      )
      sessions.value = response.patient_sessions
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { sessions, loading, error, fetchPatientSessions }
}
