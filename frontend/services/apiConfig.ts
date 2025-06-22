// API配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

// 生成API端点URL的辅助函数
export const getApiUrl = (path: string): string => {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
};
