import { useCallback, useEffect, useRef } from 'react'
import { getRequestErrorMessage, isRequestCanceled, type NormalizedUploadResponse, uploadAsset } from '../services/api'

type ImportOptions = {
  emptyResultMessage: string
  failureMessage: string
}

export function useAssetImport({
  onError,
  onImported,
  onStart,
}: {
  onError: (message: string) => void
  onImported: (result: NormalizedUploadResponse, file: File) => void
  onStart: () => void
}) {
  const controllerRef = useRef<AbortController | null>(null)

  const abortActiveImport = useCallback(() => {
    controllerRef.current?.abort()
  }, [])

  useEffect(() => () => {
    controllerRef.current?.abort()
  }, [])

  const importFile = useCallback(async (file: File, options: ImportOptions) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    onStart()

    try {
      const result = await uploadAsset(file, { signal: controller.signal })
      if (!result.mediaUrl) {
        onError(options.emptyResultMessage)
        return false
      }

      onImported(result, file)
      return true
    } catch (error) {
      if (isRequestCanceled(error)) {
        return false
      }

      onError(getRequestErrorMessage(error, options.failureMessage))
      return false
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null
      }
    }
  }, [onError, onImported, onStart])

  const openPicker = useCallback((accept: string, options: ImportOptions) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      await importFile(file, options)
    }
    input.click()
  }, [importFile])

  const importFromClipboard = useCallback(async (
    files: File[],
    matcher: (file: File) => boolean,
    options: ImportOptions
  ) => {
    const file = files.find(matcher)
    if (!file) return false
    return importFile(file, options)
  }, [importFile])

  return {
    abortActiveImport,
    importFromClipboard,
    openPicker,
  }
}
