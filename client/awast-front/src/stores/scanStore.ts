import { defineStore } from 'pinia';
import zapService from '@/services/zapService';
import userService from '@/services/userService';

export const useScanStore = defineStore('scan', {
    state: () => ({
        activeScanId: null as string | null,
        scanStatus: null as any | null,
        alerts: [] as any[],
        isScanning: false,
        scanHistory: [] as any[],
        scanResults: null as any | null,
        isLoadingHistory: false,
        isLoadingResults: false,
    }),
    actions: {
        async startSpider(target: string) {
            this.isScanning = true;
            try {
                const response = await zapService.startSpider(target);
                this.activeScanId = response.scan;
                return response;
            } catch (error) {
                this.isScanning = false;
                throw error;
            }
        },
        async startScan(target: string) {
            this.isScanning = true;
            try {
                const response = await zapService.startScan(target);
                this.activeScanId = response.scan;
                return response;
            } catch (error) {
                this.isScanning = false;
                throw error;
            }
        },
        async checkStatus() {
            if (!this.activeScanId) return;
            try {
                const status = await zapService.getScanStatus(this.activeScanId);
                this.scanStatus = status;
                if (status.status === '100') {
                    this.isScanning = false;
                }
            } catch (error) {
                console.error('Failed to check scan status', error);
            }
        },
        async loadAlerts(baseUrl?: string) {
            try {
                const alerts = await zapService.getAlerts(baseUrl);
                this.alerts = alerts;
            } catch (error) {
                throw error;
            }
        },
        async fetchAlertsSummary() {
            try {
                const summary = await zapService.getAlertsSummary();
                this.scanStatus = { ...this.scanStatus, summary };
                return summary;
            } catch (error) {
                console.error('Failed to fetch alerts summary', error);
            }
        },
        async fetchScanHistory() {
            this.isLoadingHistory = true;
            try {
                this.scanHistory = await userService.getMyScanHistory();
            } catch (error) {
                console.error('Failed to fetch scan history', error);
            } finally {
                this.isLoadingHistory = false;
            }
        },
        async fetchScanResults(scanId: string) {
            this.isLoadingResults = true;
            try {
                this.scanResults = await userService.getMyScanResults(scanId);
                return this.scanResults;
            } catch (error) {
                console.error('Failed to fetch scan results', error);
                throw error;
            } finally {
                this.isLoadingResults = false;
            }
        },
    },
});
