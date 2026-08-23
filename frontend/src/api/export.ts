import { apiClient } from './client';
import type { ExportPreviewResponse } from '../types/api';

export const getExportPreview = async (
  jobId: string,
  limit = 5
): Promise<ExportPreviewResponse> => {
  const res = await apiClient.get<ExportPreviewResponse>(`/export/${jobId}/preview`, {
    params: { limit },
  });
  return res.data;
};

export const downloadExportFile = async (
  jobId: string,
  format: 'csv' | 'xlsx' = 'csv'
): Promise<void> => {
  const res = await apiClient.post(`/export/${jobId}`, null, {
    params: { format },
    responseType: 'blob',
  });

  const blob = new Blob([res.data], {
    type:
      format === 'csv'
        ? 'text/csv;charset=utf-8;'
        : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `UniHack_Delivery_${jobId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
