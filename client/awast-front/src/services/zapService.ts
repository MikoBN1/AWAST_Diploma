import apiClient from './httpClient';
import type { RequestBody } from '@/types/api';

export default {
    async startSpider(target: string, cookies?: Record<string, string>) {
        const body: RequestBody = { target };
        if (cookies) body.cookies = cookies;
        const response = await apiClient.post('/zap/spider', body);
        return response.data;
    },

    async getSpiderStatus(scanId: string) {
        const response = await apiClient.get(`/zap/spider_status/${scanId}`);
        return response.data;
    },

    async startScan(target: string, cookies?: Record<string, string>) {
        const body: RequestBody = { target };
        if (cookies) body.cookies = cookies;
        const response = await apiClient.post('/zap/scan', body);
        return response.data;
    },

    async getScanStatus(scanId: string) {
        const response = await apiClient.get(`/zap/scan_status/${scanId}`);
        return response.data;
    },

    async getAlerts(baseUrl?: string) {
        const params = baseUrl ? { baseurl: baseUrl } : {};
        const response = await apiClient.get('/zap/alerts', { params });
        return response.data;
    },

    async getAlertsSummary() {
        const response = await apiClient.get('/zap/alerts/summary');
        return response.data;
    },

    async getAlertsTarget(baseUrl?: string) {
        const params = baseUrl ? { baseurl: baseUrl } : {};
        const response = await apiClient.get('/zap/alerts/target', { params });
        return response.data;
    },

    async getAlertById(alertId: string) {
        const response = await apiClient.get(`/zap/alerts/${alertId}`);
        return response.data;
    },

    async abortScan(scanId: string) {
        const response = await apiClient.get(`/zap/abort/scan/${scanId}`);
        return response.data;
    },
};
