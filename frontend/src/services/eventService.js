import { buildApiUrl, getAuthHeaders, parseErrorMessage, request } from './api';

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

const getEventAttendees = async (id, token) => {
  return request(
    `/events/${id}/attendees/`,
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch attendee list'
  );
};

const sendEventReminder = async (id, token) => {
  return request(
    `/events/${id}/send-reminder/`,
    {
      method: 'POST',
      headers: getAuthHeaders(token, {
        'Content-Type': 'application/json',
      }),
    },
    'Failed to send reminder emails'
  );
};

const downloadEventAttendeesCsv = async (id, token) => {
  const response = await fetch(buildApiUrl(`/events/${id}/attendees/?export=csv`), {
    headers: getAuthHeaders(token),
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Failed to export attendee list'));
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const disposition = response.headers.get('content-disposition') || '';
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
  const filename = filenameMatch?.[1] || `event-${id}-attendees.csv`;
  const link = document.createElement('a');

  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);

  return { filename };
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
  getEventAttendees,
  sendEventReminder,
  downloadEventAttendeesCsv,
  createEvent,
  updateEvent,
  deleteEvent,
  getCategories,
  approveEvent,
};

export default eventService;
