import apiClient from './httpClient';
import type { UserOut, UserCreate, UserUpdate } from '@/types/api';

export default {
    async getUsers() {
        const response = await apiClient.get<UserOut[]>('/user/all');
        return response.data;
    },

    async getMe() {
        const response = await apiClient.get<UserOut>('/user/me');
        return response.data;
    },

    async createUser(data: UserCreate) {
        const response = await apiClient.post<UserOut>('/user/new', data);
        return response.data;
    },

    async getUser(id: string) {
        const response = await apiClient.get<UserOut>(`/user/${id}`);
        return response.data;
    },

    async updateUser(id: string, data: UserUpdate) {
        const response = await apiClient.patch<UserOut>(`/user/${id}`, data);
        return response.data;
    },

    async deleteUser(id: string) {
        const response = await apiClient.delete(`/user/${id}`);
        return response.data;
    },

    async getMyScanHistory() {
        const response = await apiClient.get('/user/my/scan/history');
        return response.data;
    },

    async getMyScanResults(scanId: string) {
        const response = await apiClient.get(`/user/my/scan/${scanId}/results`);
        return response.data;
    },
};
