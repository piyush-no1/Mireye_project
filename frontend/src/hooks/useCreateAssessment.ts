import { useMutation } from '@tanstack/react-query';
import { createAssessment, CreateAssessmentPayload } from '../api/assessments';

export function useCreateAssessment() {
  return useMutation({
    mutationFn: (payload: CreateAssessmentPayload) => createAssessment(payload),
  });
}
