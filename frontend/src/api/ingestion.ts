import { apiClient } from './client';
import type {
  IngestionUploadResponse,
  ProcessingJobResponse,
  SchemaAnalysisSummary,
  PaginatedProductRecordsResponse,
} from '../types/api';

export const uploadDataset = async (file: File): Promise<IngestionUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiClient.post<IngestionUploadResponse>('/ingestion/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const listAllJobs = async (): Promise<ProcessingJobResponse[]> => {
  const res = await apiClient.get<ProcessingJobResponse[]>('/ingestion/jobs');
  return res.data;
};

export const getJobStatus = async (jobId: string): Promise<ProcessingJobResponse> => {
  const res = await apiClient.get<ProcessingJobResponse>(`/ingestion/${jobId}`);
  return res.data;
};

export const getJobSchema = async (jobId: string): Promise<SchemaAnalysisSummary> => {
  const res = await apiClient.get<SchemaAnalysisSummary>(`/ingestion/${jobId}/schema`);
  return res.data;
};

export const getJobRecords = async (
  jobId: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedProductRecordsResponse> => {
  const res = await apiClient.get<PaginatedProductRecordsResponse>(`/ingestion/${jobId}/records`, {
    params: { page, page_size: pageSize },
  });
  return res.data;
};
