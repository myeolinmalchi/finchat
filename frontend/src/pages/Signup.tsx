import { useEffect } from 'react';

import { useSearchParams } from 'react-router-dom';

export const SignupPage = () => {
  const [searchParams] = useSearchParams();

  // 액세스 토큰 발급에 사용되는 일회용 코드
  const ticket = searchParams.get('ticket');

  useEffect(() => {
    fetch('/api/v1/auth/exchange', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ ticket }),
    }).then((res) => {
      if (res.ok) {
        alert('로그인에 성공했습니다.');
      } else {
        alert('로그인 실패');
      }
    });
  }, []);

  return <></>;
};
