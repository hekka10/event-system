const API_URL = `${import.meta.env.VITE_API_URL}/dashboard`;

const getStats = async (token) => {
    const response = await fetch(`${API_URL}/stats/`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch dashboard stats');
    }
    return data;
};

const adminService = {
    getStats,
};

export default adminService;
