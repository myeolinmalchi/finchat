import { createRoot } from 'react-dom/client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppRouter } from './routes/routes.tsx';
import './styles/index.css';
import './styles/reset.css';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <AppRouter />
  </QueryClientProvider>
);
