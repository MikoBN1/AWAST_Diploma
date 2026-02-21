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

        // Dynamic WS properties
        scanProgress: 0,
        totalAlertsFound: 0,
        wsConnection: null as WebSocket | null,
        targetUrl: null as string | null,
    }),
    actions: {
        async startSpider(target: string) {
            this.isScanning = true;
            this.targetUrl = target;
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
            this.targetUrl = target;
            this.scanProgress = 0;
            this.totalAlertsFound = 0;
            this.alerts = [];

            try {
                const response = await zapService.startScan(target);
                this.activeScanId = response.scan_id;
                return response;
            } catch (error) {
                this.isScanning = false;
                throw error;
            }
        },

        connectToScanSocket(
            scanId: string,
            onComplete?: () => void,
            onError?: (msg: string) => void
        ) {
            if (this.wsConnection) {
                this.wsConnection.close();
            }

            const wsUrl = `ws://localhost:8000/api/v1/zap/ws/scan/${scanId}`;
            this.wsConnection = new WebSocket(wsUrl);

            this.wsConnection.onopen = () => {
                console.log("Connected to scan monitor.");
            };

            this.wsConnection.onmessage = (event) => {
                if (event.data === 'ping' || event.data === '"ping"') return;

                try {
                    const data = JSON.parse(event.data);

                    // If the payload contains an alerts array directly, ingest it
                    if (data.alerts && Array.isArray(data.alerts)) {
                        this.alerts = data.alerts;
                    }

                    switch (data.type) {
                        case "progress":
                            this.scanProgress = data.progress;
                            this.totalAlertsFound = data.total_alerts;

                            if (data.new_alerts && data.new_alerts.length > 0) {
                                // Add new alerts to the store reactively
                                this.alerts = [...this.alerts, ...data.new_alerts];
                            }
                            break;

                        case "done":
                            this.scanProgress = 100;
                            this.isScanning = false;
                            this.alerts = data.alerts

                            if (data.alerts_count !== undefined) {
                                this.totalAlertsFound = data.alerts_count;
                            }

                            if (this.wsConnection) {
                                this.wsConnection.close();
                                this.wsConnection = null;
                            }

                            if (onComplete) onComplete();
                            break;

                        case "error":
                            this.isScanning = false;
                            if (this.wsConnection) {
                                this.wsConnection.close();
                                this.wsConnection = null;
                            }

                            if (onError) onError(data.message || "Unknown scan error");
                            break;

                        default:
                            if (!data.type && data.alerts) {
                                // If there's no type but we have alerts, we've handled it above
                                break;
                            }
                            console.log("Unknown message type:", data);
                    }
                } catch (e) {
                    console.error("Failed to parse WS message", e);
                }
            };

            this.wsConnection.onclose = () => {
                console.log("Disconnected from scan monitor.");
                this.wsConnection = null;
            };
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
        async loadAlertById(alertId: string) {
            try {
                const alert = await zapService.getAlertById(alertId);
                return alert;
            } catch (error) {
                console.error(`Failed to load alert by ID: ${alertId}`, error);
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
