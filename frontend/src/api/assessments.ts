import { fetchApi } from './client';
import { AssessmentStatusResponse, AssessmentResult } from '../types/assessment';

export interface CreateAssessmentPayload {
  query: string;
  lat?: number;
  lng?: number;
  start_lat?: number;
  start_lng?: number;
  end_lat?: number;
  end_lng?: number;
  start_name?: string;
  end_name?: string;
}

export async function createAssessment(payload: CreateAssessmentPayload): Promise<{ run_id: string; status: string }> {
  return fetchApi<{ run_id: string; status: string }>('/assessments', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getAssessmentStatus(runId: string): Promise<AssessmentStatusResponse> {
  return fetchApi<AssessmentStatusResponse>(`/assessments/${runId}`);
}

export async function getAssessmentResult(runId: string): Promise<AssessmentResult> {
  return fetchApi<AssessmentResult>(`/assessments/${runId}/result`);
}
