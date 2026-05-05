// ─── Auth ────────────────────────────────────────────────────────────────────

export interface SignupPayload {
  hospital_id: string
  name: string
  address: string
  admin_name: string
  admin_email: string
  password: string
}

export interface LoginPayload {
  hospital_id: string
  password: string
}

export interface AuthResponse {
  token: string
}

// ─── Settings ────────────────────────────────────────────────────────────────

export interface Settings {
  hospital_id: string
  name: string
  address: string
  admin_name: string
  admin_email: string
}

export interface UpdateSettingsPayload {
  name?: string
  address?: string
  admin_name?: string
  admin_email?: string
  password?: string
}

export interface BlueprintResponse {
  url: string
}

// ─── Routers ─────────────────────────────────────────────────────────────────

export interface Router {
  id: string
  name: string
  location_x: number
  location_y: number
}

export interface RouterMapEntry {
  id: string
  location_x: number
  location_y: number
  connected_devices_count: number
}

export interface RouterHourlySession {
  router_id: string
  hour: string
  sessions_count: number
  average_session_duration: number
}

export interface CreateRouterPayload {
  router_id: string
  name: string
  location_x: number
  location_y: number
}

// ─── Devices ─────────────────────────────────────────────────────────────────

export interface Device {
  id: string
  name: string
  patient_id: string | null
}

export interface DeviceWithRouterInfo {
  id: string
  name: string
  holder_name: string
  last_record_timestamp: string
  router_id: string
  router_name: string
}

export interface CreateDevicePayload {
  device_id: string
  name: string
}

// ─── Patients ─────────────────────────────────────────────────────────────────

export interface Patient {
  id: string
  name: string
}

export interface PatientSession {
  patient_id: string
  router_id: string
  router_name: string
  start_time: string
  duration: number // seconds
}

export interface CreatePatientPayload {
  device_id: string
  name: string
}

// ─── Records ─────────────────────────────────────────────────────────────────

export interface HourlyRecord {
  hour: string
  records_count: number
}

export interface HourlyPatient {
  hour: string
  patients_count: number
}

export interface HourlySessionDuration {
  hour: string
  average_total_session_duration: number // seconds
}
