import { useEffect } from 'react';

import { useNavigate, useSearchParams } from 'react-router-dom';

import kakaoLoginButton from '@/assets/login/kakao-login.svg';

export const LoginPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 액세스 토큰 발급에 사용되는 일회용 코드
  const ticket = searchParams.get('ticket');

  useEffect(() => {
    if (ticket === null) {
      return;
    }

    fetch('/api/v1/auth/exchange', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ ticket }),
    }).then((res) => {
      if (res.ok) {
        navigate('/');
      } else {
        alert('로그인 실패');
        navigate('/');
      }
    });
  }, []);

  const loginUrl = `/api/v1/auth/kakao/login`;

  if (ticket !== null) {
    return <></>;
  }

  return (
    <div className="relative flex h-screen w-full flex-col items-center justify-center">
      <div className="text-gray7 mb-[12px] text-center text-[40px] font-[700]">
        로그인
      </div>
      <h2 className="text-center text-[24px] font-[400] text-gray5">
        원하시는 로그인 방법을 선택하세요.
      </h2>
      <div className="mt-[200px] flex justify-center">
        <a href={loginUrl}>
          <img
            src={kakaoLoginButton}
            alt="카카오 로그인"
            className="h-[90px]"
          />
        </a>
      </div>
    </div>
  );
};
