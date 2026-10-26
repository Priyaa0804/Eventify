
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

export async function loginUser(username, password) {
  const response = await api.post('auth/login/', {
    username,
    password,
  })

  const accessToken = response.data.access

  if (!accessToken) {
    throw new Error('Login response did not contain an access token.')
  }

  localStorage.setItem('access_token', accessToken)

  if (response.data.refresh) {
    localStorage.setItem('refresh_token', response.data.refresh)
  }

  return response.data
}

export async function getCurrentUser() {
  const response = await api.get('auth/me/')
  return response.data
}

export function logoutUser() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export default api

export async function getVenues() {
  const response = await api.get('venues/')
  return response.data
}

export async function getMyEvents() {
  const response = await api.get('events/my/')
  return response.data
}

export async function getPendingApprovals() {
  const response = await api.get('approvals/pending/')
  return response.data
}

export async function getCalendarEvents() {
  const response = await api.get('calendar/events/')
  return response.data
}

export async function getNotifications() {
  const response = await api.get('notifications/')
  return response.data
}
