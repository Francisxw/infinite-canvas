import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  zh: {
    translation: {
      app: {
        title: 'Infinite Studio 可视化创作画布',
      },
    },
  },
  en: {
    translation: {
      app: {
        title: 'Infinite Studio Visual Canvas',
      },
    },
  },
}

void i18n.use(initReactI18next).init({
  resources,
  lng: 'zh',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
