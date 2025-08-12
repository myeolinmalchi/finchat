import { useEffect, useState } from 'react';

import { Outlet, useLocation } from 'react-router-dom';

import { Sidebar } from '@/components/Sidebar';
import { useUserInfoStore } from '@/stores/userStore';
import Header from './Header';

export const AppLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const toggleSidebar = () => setIsSidebarOpen((v) => !v);

  const { loadUserInfo } = useUserInfoStore();
  const { pathname } = useLocation();

  useEffect(() => {
    loadUserInfo();
  }, [pathname]);

  return (
    <>
      <Header />
      <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <div className="ml-[76px] flex-1">
        <Outlet />
      </div>
    </>
  );
};
