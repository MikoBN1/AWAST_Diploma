import { defineStore } from 'pinia';
import userService from '@/services/userService';
import type { UserOut, UserCreate, UserUpdate } from '@/types/api';

export const useUserStore = defineStore('user', {
    state: () => ({
        users: [] as UserOut[],
        isLoading: false,
        error: null as string | null,
    }),
    actions: {
        async fetchUsers() {
            this.isLoading = true;
            try {
                this.users = await userService.getUsers();
            } catch (error: any) {
                this.error = error.message;
            } finally {
                this.isLoading = false;
            }
        },
        async createUser(data: UserCreate) {
            this.isLoading = true;
            try {
                const newUser = await userService.createUser(data);
                this.users.push(newUser);
            } catch (error: any) {
                this.error = error.message;
                throw error;
            } finally {
                this.isLoading = false;
            }
        },
        async deleteUser(userId: string) {
            this.isLoading = true;
            try {
                await userService.deleteUser(userId);
                this.users = this.users.filter(u => u.user_id !== userId);
            } catch (error: any) {
                this.error = error.message;
                throw error;
            } finally {
                this.isLoading = false;
            }
        },
        async updateUser(userId: string, data: UserUpdate) {
            this.isLoading = true;
            try {
                const updatedUser = await userService.updateUser(userId, data);
                const index = this.users.findIndex(u => u.user_id === userId);
                if (index !== -1) {
                    this.users[index] = updatedUser;
                }
            } catch (error: any) {
                this.error = error.message;
                throw error;
            } finally {
                this.isLoading = false;
            }
        }
    },
});
