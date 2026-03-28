import { getAuthHeaders, request } from './api';

const getMyVerification = async (token) => {
  return request(
    '/student/status/',
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch student verification'
  );
};

const submitVerification = async (formData, token) => {
  return request(
    '/student/submit/',
    {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: formData,
    },
    'Failed to submit student verification'
  );
};

const getPendingVerifications = async (token, status = 'PENDING') => {
  return request(
    `/auth/student-verifications/admin/?status=${status}`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch student verifications'
  );
};

const reviewVerification = async (id, payload, token) => {
  return request(
    '/student/approve/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({
        verification_id: id,
        ...payload,
      }),
    },
    'Failed to review student verification'
  );
};

const studentService = {
  getMyVerification,
  submitVerification,
  getPendingVerifications,
  reviewVerification,
};

export default studentService;
