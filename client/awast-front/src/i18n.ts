import { createI18n } from 'vue-i18n'
import en from './i18n/en.json'
import kz from './i18n/kz.json'

const savedLocale = localStorage.getItem('locale') || 'en'

const i18n = createI18n({
    legacy: false,
    locale: savedLocale,
    fallbackLocale: 'en',
    messages: {
        en,
        kz
    }
})

export default i18n