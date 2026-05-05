import { ref } from 'vue'
import { postData } from '../api/http'
import type { LoginPayload, SignupPayload, AuthResponse } from '../types'

export function useLogin() {
  const data = ref<AuthResponse | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function login(payload: LoginPayload): Promise<AuthResponse> {
    loading.value = true
    error.value = undefined
    try {
      const response = await postData<AuthResponse>('/auth/login', payload)
      data.value = response
      localStorage.setItem('token', response.token)
      localStorage.setItem('hospitalId', payload.hospital_id)
      return response
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    localStorage.removeItem('token')
    data.value = undefined
  }

  return { data, loading, error, login, logout }
}

export function useSignup() {
  const data = ref<AuthResponse | undefined>(undefined)
  const loading = ref(false)
  const error = ref<string | undefined>(undefined)

  async function signup(payload: SignupPayload): Promise<AuthResponse> {
    loading.value = true
    error.value = undefined
    try {
      const response = await postData<AuthResponse>('/auth/signup', payload)
      data.value = response
      localStorage.setItem('token', response.token)
      localStorage.setItem('hospitalId', payload.hospital_id)
      return response
    } catch (err) {
      error.value = (err as Error).message
      throw err
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, signup }
}
