import { getAuthHeaders, request } from './api';

const createBooking = async (bookingData, token) => {
  return request(
    '/bookings/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(bookingData),
    },
    'Failed to create booking'
  );
};

const getMyBookings = async (token) => {
  return request(
    '/bookings/',
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch bookings'
  );
};

const getBookingById = async (id, token) => {
  return request(
    `/bookings/${id}/`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch booking'
  );
};

const initiatePayment = async (payload, token) => {
  return request(
    '/payments/initiate/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Failed to start checkout'
  );
};

const getPayment = async (paymentId, token) => {
  return request(
    `/payments/${paymentId}/`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch payment details'
  );
};

const verifyPayment = async (paymentId, payload, token) => {
  return request(
    '/payments/verify/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({
        payment_id: paymentId,
        ...payload,
      }),
    },
    'Failed to verify payment'
  );
};

const createOfflineBooking = async (payload, token) => {
  return request(
    '/bookings/offline/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Failed to create offline booking'
  );
};

const scanTicket = async (payload, token) => {
  return request(
    '/bookings/tickets/scan/',
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Failed to scan ticket'
  );
};

const bookingService = {
  createBooking,
  getMyBookings,
  getBookingById,
  initiatePayment,
  getPayment,
  verifyPayment,
  createOfflineBooking,
  scanTicket,
};

export default bookingService;
