import { useCallback } from 'react'
import { uploadAsset } from '../services/api'

export function useFileUpload() {
  const upload = useCallback(async (file: File) => {
    return uploadAsset(file)
  }, [])

  return { upload }
}
