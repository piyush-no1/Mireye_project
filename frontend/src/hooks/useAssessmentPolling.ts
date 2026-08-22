import { useQuery } from '@tanstack/react-query';
import { getAssessmentStatus, getAssessmentResult } from '../api/assessments';
import { AssessmentResult } from '../types/assessment';

export function useAssessmentPolling(runId: string | null) {
  // 1. Poll status
  const statusQuery = useQuery({
    queryKey: ['assessment-status', runId],
    queryFn: () => getAssessmentStatus(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'needs_clarification') {
        return false; // Stop polling when finished
      }
      return 2000;
    },
  });

  const isCompleted = statusQuery.data?.status === 'completed' || statusQuery.data?.status === 'needs_clarification';

  // 2. Fetch full result when completed
  const resultQuery = useQuery({
    queryKey: ['assessment-result', runId],
    queryFn: () => getAssessmentResult(runId!),
    enabled: !!runId && isCompleted,
    retry: 3,
  });

  return {
    status: statusQuery.data?.status || 'pending',
    error: statusQuery.error || resultQuery.error || statusQuery.data?.error,
    isLoading: statusQuery.isLoading || (isCompleted && !resultQuery.data),
    result: resultQuery.data as AssessmentResult | undefined,
  };
}
