import { defineStore } from 'pinia';
import authService from '@/services/authService';
import userService from '@/services/userService';
import type { UserLogin, UserOut } from '@/types/api';

const getLocalToken = () => {
    return localStorage.getItem('token');
};

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null as UserOut | null,
        token: getLocalToken() as string | null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 'admin',
    },
    actions: {
        async login(credentials: UserLogin) {
            try {
                const response = await authService.login(credentials);
                this.token = response.access_token; // Assuming the response has access_token
                if (this.token) {
                    localStorage.setItem('token', this.token);
                    await this.fetchProfile();
                }
                return response;
            } catch (error) {
                throw error;
            }
        },
        async fetchProfile() {
            try {
                const user = await userService.getMe();
                this.user = user;
            } catch (error) {
                this.logout();
            }
        },
        logout() {
            this.user = null;
            this.token = null;
            localStorage.removeItem('token');
        },
    },
});
