import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { AssessmentPage } from './pages/AssessmentPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import './styles/global.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <ErrorBoundary>
          <AssessmentPage />
        </ErrorBoundary>
      </Layout>
    </QueryClientProvider>
  );
}

export default App;
