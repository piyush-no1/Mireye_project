import { useMutation } from '@tanstack/react-query';
import { createAssessment } from '../api/assessments';

export function useCreateAssessment() {
  return useMutation({
    mutationFn: (payload: { query: string; lat?: number; lng?: number }) => createAssessment(payload),
  });
}
