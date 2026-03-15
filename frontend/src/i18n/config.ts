import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  zh: {
    translation: {
      app: {
        title: '无限画布创作平台',
      },
    },
  },
  en: {
    translation: {
      app: {
        title: 'Infinite Canvas Platform',
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
