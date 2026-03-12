import apiClient from './httpClient';
import type { ChainAnalysisResult } from '@/types/api';

export default {
    async analyzeChains(alerts: any[]): Promise<ChainAnalysisResult> {
        const response = await apiClient.post<ChainAnalysisResult>('/chains/analyze', { alerts });
        return response.data;
    },
};
