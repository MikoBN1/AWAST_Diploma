import apiClient from './httpClient';
import type { UserLogin } from '@/types/api';

export default {
    async login(credentials: UserLogin) {
        const response = await apiClient.post('/auth/login', credentials);
        return response.data;
    },

    async refreshToken(refreshToken: string) {
        const response = await apiClient.post('/auth/refresh', {
            refresh_token: refreshToken, // Adjust field name if swagger differs slightly, but typically it is sent as json
        });
        return response.data;
    },
};
