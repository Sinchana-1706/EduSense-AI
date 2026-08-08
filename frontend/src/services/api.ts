export interface HealthCheckResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  services: {
    api: string;
    database: string;
    ai_engine: string;
  };
}

const API_BASE_URL = 'http://127.0.0.1:8000';

export async function fetchBackendHealth(): Promise<HealthCheckResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch backend health status:', error);
    throw error;
  }
}
