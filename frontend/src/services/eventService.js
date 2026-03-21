const API_URL = `${import.meta.env.VITE_API_URL}/events`;

const parseErrorMessage = (data, fallbackMessage) => {
    if (!data) {
        return fallbackMessage;
    }

    if (typeof data === 'string') {
        return data;
    }

    if (data.message) {
        return data.message;
    }

    const firstEntry = Object.entries(data)[0];
    if (!firstEntry) {
        return fallbackMessage;
    }

    const [field, messages] = firstEntry;
    if (Array.isArray(messages)) {
        return `${field}: ${messages.join(', ')}`;
    }

    return `${field}: ${messages}`;
};

const getAllEvents = async (category = '') => {
    const url = category ? `${API_URL}/?category=${category}` : API_URL;
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch events');
    }
    return data;
};

const getEventById = async (id) => {
    const response = await fetch(`${API_URL}/${id}/`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch event');
    }
    return data;
};

const createEvent = async (eventData, token) => {
    const response = await fetch(`${API_URL}/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: eventData, // FormData for images
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(parseErrorMessage(data, 'Failed to create event'));
    }
    return data;
};

const updateEvent = async (id, eventData, token) => {
    const response = await fetch(`${API_URL}/${id}/`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: eventData, // FormData for images
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(parseErrorMessage(data, 'Failed to update event'));
    }
    return data;
};

const deleteEvent = async (id, token) => {
    const response = await fetch(`${API_URL}/${id}/`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    if (!response.ok) {
        const data = await response.json();
        throw new Error(parseErrorMessage(data, 'Failed to delete event'));
    }
    return true;
};

const getCategories = async () => {
    const response = await fetch(`${API_URL}/categories/`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch categories');
    }
    return data;
};

const approveEvent = async (id, token) => {
    const response = await fetch(`${API_URL}/${id}/approve/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(parseErrorMessage(data, 'Failed to approve event'));
    }
    return data;
};

const eventService = {
    getAllEvents,
    getEventById,
    createEvent,
    updateEvent,
    deleteEvent,
    getCategories,
    approveEvent,
};

export default eventService;
