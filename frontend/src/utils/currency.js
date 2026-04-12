export const formatNpr = (value, options = {}) => {
  const { allowFree = false } = options;
  const amount = Number(value ?? 0);

  if (!Number.isFinite(amount)) {
    return allowFree ? 'Free' : 'NRs 0.00';
  }

  if (allowFree && amount <= 0) {
    return 'Free';
  }

  return `NRs ${amount.toFixed(2)}`;
};
