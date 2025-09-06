import axios, { AxiosError, AxiosRequestConfig } from 'axios';

export const fetchInstance = axios.create({
  //baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

fetchInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    console.error('에러:', error);

    return Promise.reject(error);
  }
);

fetchInstance.interceptors.response.use(
  (response) => {
    return { ...response.data, status: response.status };
  },
  async (error: AxiosError) => {
    console.error('에러:', error);

    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: boolean;
    };

    // refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        //await fetchInstance.post('/api/v1/auth/token/refresh', {});
        //return fetchInstance(originalRequest);
      } catch (refreshError) {
        console.error('토큰 재발급 실패:', refreshError);
        window.location.href = '/login';
      }
    }

    return Promise.reject(
      error.response?.data || {
        message: '알 수 없는 오류가 발생했습니다.',
        status: 500,
      }
    );
  }
);
