import { defineStore } from 'pinia'

export const useConfigStore = defineStore('config', {
  state: () => ({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  })
})
