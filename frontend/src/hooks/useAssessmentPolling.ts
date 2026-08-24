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
        return false; // Stop polling when fully finished
      }
      return 2000;
    },
  });

  const isPartiallyOrFullyCompleted = statusQuery.data?.status === 'assessment_completed' || 
                                      statusQuery.data?.status === 'completed' || 
                                      statusQuery.data?.status === 'needs_clarification';

  // 2. Fetch full result when partially or fully completed
  // We want to refetch the result file whenever status changes from assessment_completed to completed
  const resultQuery = useQuery({
    queryKey: ['assessment-result', runId, statusQuery.data?.status],
    queryFn: () => getAssessmentResult(runId!),
    enabled: !!runId && isPartiallyOrFullyCompleted,
    retry: 3,
  });

  return {
    status: statusQuery.data?.status || 'pending',
    error: statusQuery.error || resultQuery.error || statusQuery.data?.error,
    isLoading: statusQuery.isLoading || (isPartiallyOrFullyCompleted && !resultQuery.data),
    result: resultQuery.data as AssessmentResult | undefined,
  };
}
