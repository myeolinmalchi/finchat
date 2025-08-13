import { useState } from 'react';

import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useUserInfoStore } from '@/stores/userStore';

type HeaderDropDownButtonProps = {
  children: React.ReactNode;
  onClick?: () => void;
};

const HeaderDropDownButton = ({
  children,
  onClick,
}: HeaderDropDownButtonProps) => {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center justify-center rounded-[12px] py-[8px] hover:bg-gray-200"
    >
      {children}
    </button>
  );
};

type HeaderDropDownProps = {
  visible: boolean;
};

const HeaderDropDown = ({ visible }: HeaderDropDownProps) => {
  const { logout } = useUserInfoStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate(0);
  };

  if (!visible) {
    return <></>;
  }

  return (
    <div className="absolute right-0 top-[calc(100%+12px)] flex w-[120px] flex-col items-center justify-center gap-[12px] rounded-[16px] border-[1px] border-gray-300 p-[8px]">
      <HeaderDropDownButton onClick={handleLogout}>
        로그아웃
      </HeaderDropDownButton>
    </div>
  );
};

const HeaderContainer = ({ children }: { children?: React.ReactNode }) => {
  return (
    <div className="fixed right-0 top-0 z-20 flex h-[32px] box-content w-[calc(100vw-76px)] items-center justify-end pr-[60px] pt-[36px]">
      {children}
    </div>
  );
};

const Header = () => {
  const [isDropdownVisible, setDropdownVisible] = useState(false);
  const toggleDropdown = () => setDropdownVisible(!isDropdownVisible);

  const { userInfo, isPending } = useUserInfoStore();
  const { pathname } = useLocation();

  const isHeaderVisible = !pathname.startsWith('/login')

  if (!isHeaderVisible) {
    return <></>;
  }

  if (userInfo === null && isPending) {
    return <HeaderContainer />;
  }

  if (userInfo === null) {
    return (
      <HeaderContainer>
        <Link
          to="/login"
          className="text-[16px] font-[700] text-gray7 animate-fade-in"
        >
          로그인
        </Link>
      </HeaderContainer>
    );
  }

  return (
    <HeaderContainer>
      <button
        onClick={toggleDropdown}
        className="relative flex animate-fade-in items-center justify-center gap-[8px]"
      >
        <HeaderDropDown visible={isDropdownVisible} />
        <img
          src={userInfo?.profile_image_url}
          className="h-8 w-8 rounded-full bg-gray-100"
        />
        <span className="text-[16px] font-[700] text-[#333534]">
          {userInfo.name ?? userInfo.nickname}
        </span>
      </button>
    </HeaderContainer>
  );
};

export default Header;
