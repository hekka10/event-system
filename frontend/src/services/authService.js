const API_URL = `${import.meta.env.VITE_API_URL}/auth`;

const register = async (userData) => {
    const response = await fetch(`${API_URL}/register/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Signup failed');
    }
    return data;
};

const login = async (userData) => {
    const response = await fetch(`${API_URL}/login/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Login failed');
    }

    if (data.access) {
        localStorage.setItem('user', JSON.stringify(data));
    }

    return data;
};

const logout = () => {
    localStorage.removeItem('user');
};

const getCurrentUser = () => {
    return JSON.parse(localStorage.getItem('user'));
};

const authService = {
    register,
    login,
    logout,
    getCurrentUser,
};

export default authService;

