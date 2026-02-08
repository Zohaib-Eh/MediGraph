import useSWR from "swr"
import { api } from "./api"

export function useHealth() {
  return useSWR("health", () => api.health(), {
    refreshInterval: 30000,
    errorRetryCount: 2,
  })
}

export function useStats() {
  return useSWR("stats", () => api.stats(), {
    refreshInterval: 15000,
    errorRetryCount: 2,
    dedupingInterval: 0,
  })
}

export function useMedicalDeserts() {
  return useSWR("medical-deserts", () => api.medicalDeserts())
}

export function useEquipmentGaps() {
  return useSWR("equipment-gaps", () => api.equipmentGaps())
}

export function useInconsistencies() {
  return useSWR("inconsistencies", () => api.inconsistencies())
}
