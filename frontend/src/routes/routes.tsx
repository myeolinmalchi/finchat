import {
  Navigate,
  RouterProvider,
  createBrowserRouter,
} from 'react-router-dom';

import { AppLayout } from '@/layouts/AppLayout';

import { FeedPage } from '@/pages/Feed';
import { HomePage } from '@/pages/Home';
import { LoginPage } from '@/pages/Login';
import { SignupPage } from '@/pages/Signup';

import { RouterPath } from './path';

const router = createBrowserRouter([
  {
    path: RouterPath.ROOT,
    element: <AppLayout />,
    children: [
      {
        path: RouterPath.HOME,
        element: <HomePage />,
      },
      {
        path: RouterPath.CHAT_DETAIL,
        element: <HomePage />,
      },
      {
        path: RouterPath.LOGIN,
        element: <LoginPage />,
      },
      {
        path: RouterPath.FEED,
        element: <FeedPage />,
      },
    ],
  },
  {
    path: RouterPath.NOT_FOUND,
    element: <Navigate to={RouterPath.HOME} />,
  },
]);

export const AppRouter = () => <RouterProvider router={router} />;
