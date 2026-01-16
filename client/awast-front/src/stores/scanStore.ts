import { defineStore } from 'pinia';
import zapService from '@/services/zapService';

export const useScanStore = defineStore('scan', {
    state: () => ({
        activeScanId: null as string | null,
        scanStatus: null as any | null,
        alerts: [] as any[],
        isScanning: false,
    }),
    actions: {
        async startSpider(target: string) {
            this.isScanning = true;
            try {
                const response = await zapService.startSpider(target);
                this.activeScanId = response.scan; // Adjust based on actual response field
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
                this.activeScanId = response.scan; // Adjust based on actual response field
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
                if (status.status === '100') { // Assuming '100' means complete
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
                // const summary = await zapService.getAlertsSummary();
                const summary = {
                    High: 5,
                    Medium: 12,
                    Low: 25,
                    Informational: 10
                };
                this.scanStatus = { ...this.scanStatus, summary }; // Storing summary in scanStatus or a new state
                return summary;
            } catch (error) {
                console.error('Failed to fetch alerts summary', error);
            }
        }
    },
});
