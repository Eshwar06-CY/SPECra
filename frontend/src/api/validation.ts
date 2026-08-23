import { apiClient } from './client';
import type { ValidationReportResponse } from '../types/api';

export const validateProduct = async (
  productId: string
): Promise<ValidationReportResponse> => {
  const res = await apiClient.post<ValidationReportResponse>(
    `/validation/product/${productId}`
  );
  return res.data;
};

export const getProductValidation = async (
  productId: string
): Promise<ValidationReportResponse> => {
  const res = await apiClient.get<ValidationReportResponse>(
    `/validation/product/${productId}`
  );
  return res.data;
};
