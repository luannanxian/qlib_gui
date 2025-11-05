/**
 * User Mode API Functions
 *
 * API calls for user mode and preferences management
 */

import { apiClient } from './client';
import type {
  APIResponse,
  ModeUpdateRequest,
  ModeResponse,
  PreferencesUpdateRequest,
  PreferencesResponse,
} from '@/types/api';

export const userModeApi = {
  /**
   * Get current user mode
   */
  getMode: async (userId: string): Promise<ModeResponse> => {
    const { data } = await apiClient.get<APIResponse<ModeResponse>>('/api/user/mode', {
      params: { user_id: userId },
    });
    return data.data!;
  },

  /**
   * Update user mode (switch between BEGINNER and EXPERT)
   */
  updateMode: async (userId: string, request: ModeUpdateRequest): Promise<ModeResponse> => {
    const { data } = await apiClient.post<APIResponse<ModeResponse>>(
      '/api/user/mode',
      request,
      {
        params: { user_id: userId },
      }
    );
    return data.data!;
  },

  /**
   * Get user preferences
   */
  getPreferences: async (userId: string): Promise<PreferencesResponse> => {
    const { data } = await apiClient.get<APIResponse<PreferencesResponse>>(
      '/api/user/preferences',
      {
        params: { user_id: userId },
      }
    );
    return data.data!;
  },

  /**
   * Update user preferences (partial update supported)
   */
  updatePreferences: async (
    userId: string,
    request: PreferencesUpdateRequest
  ): Promise<PreferencesResponse> => {
    const { data } = await apiClient.put<APIResponse<PreferencesResponse>>(
      '/api/user/preferences',
      request,
      {
        params: { user_id: userId },
      }
    );
    return data.data!;
  },
};
