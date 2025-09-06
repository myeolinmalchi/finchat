import { useEffect } from 'react';

import { Outlet, useLocation } from 'react-router-dom';

import { useUserInfoStore } from '@/stores/userStore';

import Header from './Header';

const Layout = () => {
  const { loadUserInfo } = useUserInfoStore();
  const { pathname } = useLocation();

  useEffect(() => {
    loadUserInfo();
  }, [pathname]);

  return (
    <div className="relative flex h-screen overflow-hidden bg-white">
      <Header />
      <Outlet />
    </div>
  );
};

export default Layout;
