import apiClient from './httpClient';
import type { ReportRequest, DownloadReportRequest } from '@/types/api';

export default {
    async generateReport(scanId: string) {
        const response = await apiClient.post('/report/new', { scan_id: scanId } as ReportRequest);
        return response.data;
    },

    async downloadReport(reportId: string) {
        const response = await apiClient.post('/report/download', { report_id: reportId } as DownloadReportRequest, {
            responseType: 'blob', // Important for downloading files
        });
        return response.data;
    },
};
