import apiClient from './httpClient';

export const swaggerService = {
    async analyzeSwagger(file: File) {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await apiClient.post('/analyze/swagger', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        } catch (error) {
            console.error('Error analyzing swagger file:', error);
            throw error;
        }
    },
};
