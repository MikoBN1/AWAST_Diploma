import {createRouter, createWebHistory} from 'vue-router'
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ScannerView from "../views/ScannerView.vue";

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL || 'localhost'),
    routes: [
        {
            path: '/auth/login',
            name: 'login',
            component: LoginView,
            meta: { hideHeader: true }
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: DashboardView,
            meta: { hideHeader: false }
        },
        {
            path: '/scanner',
            name: 'scanner',
            component: ScannerView,
            meta: { hideHeader: false }
        }
    ]
})

export default router