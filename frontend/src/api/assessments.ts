import { fetchApi } from './client';
import { AssessmentStatusResponse, AssessmentResult } from '../types/assessment';

export async function createAssessment(query: string): Promise<{ run_id: string; status: string }> {
  return fetchApi<{ run_id: string; status: string }>('/assessments', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

export async function getAssessmentStatus(runId: string): Promise<AssessmentStatusResponse> {
  return fetchApi<AssessmentStatusResponse>(`/assessments/${runId}`);
}

export async function getAssessmentResult(runId: string): Promise<AssessmentResult> {
  return fetchApi<AssessmentResult>(`/assessments/${runId}/result`);
}
