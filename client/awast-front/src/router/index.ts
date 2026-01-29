import { createRouter, createWebHistory } from 'vue-router'
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ScannerView from "../views/ScannerView.vue";
import SwaggerAnalysisView from "../views/SwaggerAnalysisView.vue";

import ScanHistoryView from "../views/ScanHistoryView.vue";
import ProfileView from "../views/ProfileView.vue";

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
        },
        {
            path: '/exploiter',
            name: 'exploiter',
            component: () => import('../views/ExploiterView.vue'),
            meta: { hideHeader: false }
        },
        {
            path: '/swagger-analysis',
            name: 'swagger-analysis',
            component: SwaggerAnalysisView,
            meta: { hideHeader: false }
        },
        {
            path: '/scanner/history',
            name: 'scanner_history',
            component: ScanHistoryView,
            meta: { hideHeader: false }
        },
        {
            path: '/scanner/history/:id',
            name: 'scan_details',
            component: () => import('../views/ScanDetailsView.vue'),
            meta: { hideHeader: false }
        },
        {
            path: '/profile',
            name: 'profile',
            component: ProfileView,
            meta: { hideHeader: false }
        },
        {
            path: '/admin/users',
            name: 'admin_users',
            component: () => import('../views/AdminUsersView.vue'),
            meta: { hideHeader: false }
        }
    ]
})

export default router