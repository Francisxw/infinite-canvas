import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { type AccountPackage, type AccountProfile, type AccountLedgerEntry, type RechargeOrder } from '../services/api'

type PendingRechargeOrder = {
  order: RechargeOrder
  package: AccountPackage | null
  codeUrl: string | null
}

type AccountState = {
  token: string | null
  profile: AccountProfile | null
  ledger: AccountLedgerEntry[]
  packages: AccountPackage[]
  pendingRechargeOrder: PendingRechargeOrder | null
  setSession: (payload: { token: string; profile: AccountProfile; ledger?: AccountLedgerEntry[] }) => void
  setProfile: (profile: AccountProfile) => void
  setLedger: (ledger: AccountLedgerEntry[]) => void
  setPackages: (packages: AccountPackage[]) => void
  setPendingRechargeOrder: (order: PendingRechargeOrder | null) => void
  syncPoints: (points: number) => void
  clearSession: () => void
}

export const ACCOUNT_STORAGE_KEY = 'infinite-canvas-account'

export type PersistedAccountState = Pick<AccountState, 'token' | 'profile'>

export function partializeAccountState(state: AccountState): PersistedAccountState {
  return {
    token: state.token,
    profile: state.profile,
  }
}

export const useAccountStore = create<AccountState>()(
  persist(
    (set) => ({
      token: null,
      profile: null,
      ledger: [],
      packages: [],
      pendingRechargeOrder: null,
      setSession: ({ token, profile, ledger = [] }) => set({ token, profile, ledger }),
      setProfile: (profile) => set({ profile }),
      setLedger: (ledger) => set({ ledger }),
      setPackages: (packages) => set({ packages }),
      setPendingRechargeOrder: (pendingRechargeOrder) => set({ pendingRechargeOrder }),
      syncPoints: (points) =>
        set((state) => ({
          profile: state.profile ? { ...state.profile, points } : state.profile,
        })),
      clearSession: () => set({ token: null, profile: null, ledger: [], packages: [], pendingRechargeOrder: null }),
    }),
    {
      // Transitional browser-scoped bearer persistence until cookie-first auth is fully wired.
      name: ACCOUNT_STORAGE_KEY,
      partialize: partializeAccountState,
    }
  )
)
