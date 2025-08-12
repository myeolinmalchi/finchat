import { useState } from 'react';

import { Outlet } from 'react-router-dom';

import { Sidebar } from '@/components/Sidebar';

export const AppLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const toggleSidebar = () => setIsSidebarOpen((v) => !v);

  return (
    <>
      <div className="fixed right-[60px] top-[36px] z-50 flex items-center gap-[8px]">
        <div className="h-8 w-8 rounded-full bg-[#D9D9D9]" />
        <span className="text-[16px] font-[700] text-[#333534]">
          이용자 이름
        </span>
      </div>

      <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />

      <div className="ml-[76px] flex-1">
        <Outlet />
      </div>
    </>
  );
};
