import apiClient from './httpClient';
import type { UserOut, UserCreate, UserUpdate } from '@/types/api';

export default {
    async getUsers() {
        const response = await apiClient.get<UserOut[]>('/api/user/all');
        return response.data;
    },

    async getMe() {
        const response = await apiClient.get<UserOut>('/api/user/me');
        return response.data;
    },

    async createUser(data: UserCreate) {
        const response = await apiClient.post<UserOut>('/api/user/new', data);
        return response.data;
    },

    async getUser(id: string) {
        const response = await apiClient.get<UserOut>(`/api/user/${id}`);
        return response.data;
    },

    async updateUser(id: string, data: UserUpdate) {
        const response = await apiClient.patch<UserOut>(`/api/user/${id}`, data);
        return response.data;
    },

    async deleteUser(id: string) {
        const response = await apiClient.delete(`/api/user/${id}`);
        return response.data;
    },

    async getMyScanHistory() {
        const response = await apiClient.get('/api/user/my/scan/history');
        return response.data;
    },

    async getMyScanResults(scanId: string) {
        const response = await apiClient.get(`/api/user/my/scan/${scanId}/results`);
        return response.data;
    },
};
