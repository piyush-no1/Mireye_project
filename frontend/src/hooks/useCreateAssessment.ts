import { useMutation } from '@tanstack/react-query';
import { createAssessment } from '../api/assessments';

export function useCreateAssessment() {
  return useMutation({
    mutationFn: (query: string) => createAssessment(query),
  });
}
