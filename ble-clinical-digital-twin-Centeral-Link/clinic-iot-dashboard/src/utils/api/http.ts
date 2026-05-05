import router from "@/router"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000'

function getToken(): string | null {
  return localStorage.getItem('token')
}

function isAuthEndpoint(endpoint: string): boolean {
  return endpoint.startsWith('/auth/')
}

function buildHeaders(endpoint: string, isFormData = false): HeadersInit {
  const headers: Record<string, string> = {}

  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  if (!isAuthEndpoint(endpoint)) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  // 401 Unauthorized
  if (response.status === 401) {
    localStorage.removeItem('token')
    router.push('/auth')
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error?.message ?? error?.error ?? `HTTP error ${response.status}`)
  }
  // 204 No Content
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function getData<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'GET',
    headers: buildHeaders(endpoint),
  })
  return handleResponse<T>(response)
}

export async function postData<T>(endpoint: string, data: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: buildHeaders(endpoint),
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function putData<T>(endpoint: string, data: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'PUT',
    headers: buildHeaders(endpoint),
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function putFile<T>(endpoint: string, file: File, fieldName = 'image'): Promise<T> {
  const formData = new FormData()
  formData.append(fieldName, file)

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'PUT',
    headers: buildHeaders(endpoint, true),
    body: formData,
  })
  return handleResponse<T>(response)
}

export async function deleteData<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: buildHeaders(endpoint),
  })
  return handleResponse<T>(response)
}
