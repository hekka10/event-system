import { getAuthHeaders, request } from './api';

const getStats = async (token) => {
  return request(
    '/dashboard/stats/',
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch dashboard stats'
  );
};

const adminService = {
  getStats,
};

export default adminService;
