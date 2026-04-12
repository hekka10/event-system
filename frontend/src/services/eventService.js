import { getAuthHeaders, request } from './api';

const getAllEvents = async (category = '', token = '') => {
  const query = category ? `?category=${category}` : '';
  return request(
    `/events/${query}`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch events'
  );
};

const getEventById = async (id, token = '') => {
  return request(
    `/events/${id}/`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch event'
  );
};

const getRecommendedEvents = async (token) => {
  return request(
    '/events/recommended/',
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch recommended events'
  );
};

const createEvent = async (eventData, token) => {
  return request(
    '/events/',
    {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: eventData,
    },
    'Failed to create event'
  );
};

const updateEvent = async (id, eventData, token) => {
  return request(
    `/events/${id}/`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(token),
      body: eventData,
    },
    'Failed to update event'
  );
};

const deleteEvent = async (id, token) => {
  return request(
    `/events/${id}/`,
    {
      method: 'DELETE',
      headers: getAuthHeaders(token),
    },
    'Failed to delete event'
  );
};

const getCategories = async () => {
  return request('/events/categories/', {}, 'Failed to fetch categories');
};

const approveEvent = async (id, token) => {
  return request(
    `/events/${id}/approve/`,
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
    },
    'Failed to approve event'
  );
};

const eventService = {
  getAllEvents,
  getEventById,
  getRecommendedEvents,
  createEvent,
  updateEvent,
  deleteEvent,
  getCategories,
  approveEvent,
};

export default eventService;
