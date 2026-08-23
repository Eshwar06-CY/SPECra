import axios from 'axios';
import type {
  ProcessingJob,
  ProductDetail,
  ValidationReport,
  EnrichmentReport,
  ExportPreview,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
});

export const getHealth = async () => {
  const res = await api.get('/intelligence/health');
  return res.data;
};

// Jobs & Ingestion
export const getJobs = async (): Promise<ProcessingJob[]> => {
  const res = await api.get('/ingestion/jobs');
  return res.data;
};

export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/ingestion/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

// Intelligence Extraction
export const analyzeJob = async (jobId: string, limit?: number, productId?: string) => {
  let url = `/intelligence/analyze/${jobId}`;
  const params: any = {};
  if (limit) params.limit = limit;
  if (productId) params.product_id = productId;
  const res = await api.post(url, null, { params });
  return res.data;
};

export const analyzeSingleProduct = async (productId: string) => {
  const res = await api.post(`/intelligence/analyze/product/${productId}`);
  return res.data;
};

export const getProductIntelligence = async (productId: string): Promise<ProductDetail> => {
  const res = await api.get(`/intelligence/product/${productId}`);
  return res.data;
};

// Validation
export const validateProduct = async (productId: string): Promise<ValidationReport> => {
  const res = await api.post(`/validation/product/${productId}`);
  return res.data;
};

export const getProductValidation = async (productId: string): Promise<ValidationReport> => {
  const res = await api.get(`/validation/product/${productId}`);
  return res.data;
};

// Enrichment
export const enrichProduct = async (productId: string): Promise<EnrichmentReport> => {
  const res = await api.post(`/enrichment/product/${productId}`);
  return res.data;
};

export const getProductEnrichment = async (productId: string): Promise<EnrichmentReport> => {
  const res = await api.get(`/enrichment/product/${productId}`);
  return res.data;
};

// Export & Delivery
export const getExportPreview = async (jobId: string, limit = 5): Promise<ExportPreview> => {
  const res = await api.get(`/export/${jobId}/preview`, { params: { limit } });
  return res.data;
};

export const downloadExport = async (jobId: string, format: 'csv' | 'xlsx' = 'csv') => {
  const res = await api.post(`/export/${jobId}`, null, {
    params: { format },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `UniHack_Delivery_${jobId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
