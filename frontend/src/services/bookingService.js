const API_URL = `${import.meta.env.VITE_API_URL}/bookings`;

const createBooking = async (bookingData, token) => {
    const response = await fetch(`${API_URL}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(bookingData),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to create booking');
    }
    return data;
};

const getMyBookings = async (token) => {
    const response = await fetch(`${API_URL}/`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch bookings');
    }
    return data;
};

const getBookingById = async (id, token) => {
    const response = await fetch(`${API_URL}/${id}/`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch booking');
    }
    return data;
};

const bookingService = {
    createBooking,
    getMyBookings,
    getBookingById,
};

export default bookingService;
