const RAW_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_URL = RAW_API_URL.endsWith('/') ? RAW_API_URL.slice(0, -1) : RAW_API_URL;

export const buildApiUrl = (path) => `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;

export const getAuthHeaders = (token, extraHeaders = {}) => ({
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
  ...extraHeaders,
});

export const parseErrorMessage = (data, fallbackMessage) => {
  if (!data) {
    return fallbackMessage;
  }

  if (typeof data === 'string') {
    return data;
  }

  if (data.detail) {
    return data.detail;
  }

  if (data.message) {
    return data.message;
  }

  if (data.non_field_errors) {
    if (Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(', ');
    }
    return String(data.non_field_errors);
  }

  const firstEntry = Object.entries(data)[0];
  if (!firstEntry) {
    return fallbackMessage;
  }

  const [field, messages] = firstEntry;
  if (Array.isArray(messages)) {
    if (field === 'non_field_errors') {
      return messages.join(', ');
    }
    return `${field}: ${messages.join(', ')}`;
  }

  if (typeof messages === 'object' && messages !== null) {
    return parseErrorMessage(messages, fallbackMessage);
  }

  if (field === 'non_field_errors') {
    return String(messages);
  }

  return `${field}: ${messages}`;
};

export const request = async (path, options = {}, fallbackMessage = 'Request failed') => {
  const response = await fetch(buildApiUrl(path), options);
  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const error = new Error(parseErrorMessage(data, fallbackMessage));
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
};
