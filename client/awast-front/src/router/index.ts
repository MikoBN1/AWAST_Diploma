import {createRouter, createWebHistory} from 'vue-router'
import LoginView from "../views/LoginView.vue";

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL || 'localhost'),
    routes: [
        {
            path: '/auth/login',
            name: 'login',
            component: LoginView,
            meta: { hideHeader: true }
        }
    ]
})

export default router