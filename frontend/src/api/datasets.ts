/**
 * Dataset API Functions
 *
 * API calls for dataset management (CRUD operations)
 */

import { apiClient } from './client';
import type {
  DatasetCreate,
  DatasetUpdate,
  DatasetResponse,
  DatasetListResponse,
  DatasetQueryParams,
} from '@/types/api';

export const datasetsApi = {
  /**
   * Get paginated list of datasets with optional filters
   */
  list: async (params?: DatasetQueryParams): Promise<DatasetListResponse> => {
    const { data } = await apiClient.get<DatasetListResponse>('/api/datasets', { params });
    return data;
  },

  /**
   * Get single dataset by ID
   */
  get: async (id: string): Promise<DatasetResponse> => {
    const { data } = await apiClient.get<DatasetResponse>(`/api/datasets/${id}`);
    return data;
  },

  /**
   * Create new dataset
   */
  create: async (dataset: DatasetCreate): Promise<DatasetResponse> => {
    const { data } = await apiClient.post<DatasetResponse>('/api/datasets', dataset);
    return data;
  },

  /**
   * Update existing dataset
   */
  update: async (id: string, dataset: DatasetUpdate): Promise<DatasetResponse> => {
    const { data } = await apiClient.put<DatasetResponse>(`/api/datasets/${id}`, dataset);
    return data;
  },

  /**
   * Delete dataset (soft delete by default)
   */
  delete: async (id: string, hardDelete = false): Promise<void> => {
    await apiClient.delete(`/api/datasets/${id}`, {
      params: { hard_delete: hardDelete },
    });
  },
};
