export type AccountSyncPayload = {
  points?: number
  refreshProfile?: boolean
}

type AuthBridgeConfig = {
  getToken: () => string | null
  onAccountSync: (payload: AccountSyncPayload) => void
  onAuthFailure: () => void
}

const defaultConfig: AuthBridgeConfig = {
  getToken: () => null,
  onAccountSync: () => undefined,
  onAuthFailure: () => undefined,
}

let currentConfig: AuthBridgeConfig = defaultConfig

export const authBridge = {
  configure(config: Partial<AuthBridgeConfig>) {
    const previousConfig = currentConfig
    currentConfig = { ...currentConfig, ...config }

    return () => {
      currentConfig = previousConfig
    }
  },

  reset() {
    currentConfig = defaultConfig
  },

  getToken() {
    return currentConfig.getToken()
  },

  syncAccount(payload: AccountSyncPayload) {
    currentConfig.onAccountSync(payload)
  },

  handleAuthFailure() {
    currentConfig.onAuthFailure()
  },
}
