const DEFAULT_LOCALE = 'en-US';

const DEFAULT_DATE_TIME_OPTIONS = {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
};

const DEFAULT_DATE_OPTIONS = {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
};

const parseDate = (value) => {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

export const formatDateTime = (
  value,
  {
    fallback = 'Not available',
    locale = DEFAULT_LOCALE,
    options = DEFAULT_DATE_TIME_OPTIONS,
  } = {}
) => {
  const date = parseDate(value);

  if (!date) {
    return fallback;
  }

  return date.toLocaleString(locale, options);
};

export const formatDate = (
  value,
  {
    fallback = 'Not available',
    locale = DEFAULT_LOCALE,
    options = DEFAULT_DATE_OPTIONS,
  } = {}
) => {
  const date = parseDate(value);

  if (!date) {
    return fallback;
  }

  return date.toLocaleDateString(locale, options);
};

export const toLocalDateTimeInputValue = (value) => {
  const date = parseDate(value);

  if (!date) {
    return '';
  }

  const timezoneOffset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16);
};
