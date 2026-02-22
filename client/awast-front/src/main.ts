import { createApp, watch } from 'vue'
import './style.css'
import App from './App.vue'
import router from "./router"
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createPinia } from "pinia"
import i18n from "./i18n.ts"
import { en, ru } from 'vuetify/locale'

const vuetify = createVuetify({
    components,
    directives,
    theme: {
        defaultTheme: 'lightTheme',
        themes: {
            lightTheme: {
                dark: false,
                colors: {
                    primary: '#1976D2',
                    secondary: '#424242',
                    background: '#F7F7F7FF',
                    surface: '#FFF',
                    error: '#FF5252',
                    success: '#4CAF50',
                    sidebar: '#1F263E',
                    card: '#2E364E',
                },
            },
            darkTheme: {
                dark: true,
                colors: {
                    primary: '#1976D2',
                    secondary: '#424242',
                    background: '#070F26',
                },
            },
        },
    },
    icons: {
        defaultSet: 'mdi',
    },
    locale: {
        locale: i18n.global.locale.value,
        fallback: 'en',
        messages: { en, ru },
    },
})

const app = createApp(App)

app.use(i18n)
app.use(createPinia())
app.use(router)
app.use(vuetify)

watch(
    () => i18n.global.locale.value,
    (newLocale) => {
        vuetify.locale.current.value = newLocale
    },
    { immediate: true }
)

app.mount('#app')

//Ollama path D:\Ollama