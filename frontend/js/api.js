/**
 * ComplianceVault - API Client
 */

// const API_BASE = window.location.origin + '/api';
const API_BASE = "https://compliancevault-production.up.railway.app/"


// Token storage
const TOKEN_KEY = 'cv_token';
const USER_KEY = 'cv_user';

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

export function getUser() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
}

export function setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
    return !!getToken();
}

// API request helper
async function request(endpoint, options = {}) {
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        clearAuth();
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized');
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
    }

    return data;
}

// File upload helper
async function uploadFile(endpoint, file) {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Upload failed');
    }

    return response.json();
}

// ============== Auth API ==============
export const auth = {
    async login(email, password) {
        const data = await request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        setToken(data.access_token);
        setUser(data.user);
        return data;
    },

    async register(userData) {
        const data = await request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        setToken(data.access_token);
        setUser(data.user);
        return data;
    },

    async forgotPassword(email) {
        return request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    },

    async resetPassword(token, newPassword) {
        return request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, new_password: newPassword })
        });
    },

    async getMe() {
        return request('/auth/me');
    },

    logout() {
        clearAuth();
        window.location.href = '/';
    }
};

// ============== Organization API ==============
export const organization = {
    async get() {
        return request('/organizations/me');
    },

    async update(data) {
        return request('/organizations/me', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async getUsers() {
        return request('/organizations/users');
    },

    async addUser(userData) {
        return request('/organizations/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async updateUser(userId, data) {
        return request(`/organizations/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async removeUser(userId) {
        return request(`/organizations/users/${userId}`, {
            method: 'DELETE'
        });
    }
};

// ============== Controls API ==============
export const controls = {
    async list(params = {}) {
        const query = new URLSearchParams(params).toString();
        return request(`/controls?${query}`);
    },

    async get(controlCode) {
        return request(`/controls/${controlCode}`);
    },

    async getDomains() {
        return request('/controls/domains');
    },

    async getCount(params = {}) {
        const query = new URLSearchParams(params).toString();
        return request(`/controls/count?${query}`);
    }
};

// ============== Evaluations API ==============
export const evaluations = {
    async list(params = {}) {
        const query = new URLSearchParams(params).toString();
        return request(`/evaluations?${query}`);
    },

    async get(controlCode) {
        return request(`/evaluations/${controlCode}`);
    },

    async update(controlCode, data) {
        return request(`/evaluations/${controlCode}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async uploadEvidence(controlCode, file) {
        return uploadFile(`/evaluations/${controlCode}/evidence`, file);
    },

    async getEvidence(controlCode) {
        return request(`/evaluations/${controlCode}/evidence`);
    },

    async deleteEvidence(controlCode, evidenceId) {
        return request(`/evaluations/${controlCode}/evidence/${evidenceId}`, {
            method: 'DELETE'
        });
    },

    async getComments(controlCode) {
        return request(`/evaluations/${controlCode}/comments`);
    },

    async addComment(controlCode, content) {
        return request(`/evaluations/${controlCode}/comments`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
};

// ============== Dashboard API ==============
export const dashboard = {
    async getOverview() {
        return request('/dashboard/overview');
    },

    async getDomain(domainCode) {
        return request(`/dashboard/domain/${domainCode}`);
    },

    async getPublicStats() {
        // Public endpoint - no auth required
        const response = await fetch(`${API_BASE}/dashboard/public`);
        return response.json();
    }
};

// ============== History API ==============
export const history = {
    async list(entityType = null, limit = 100) {
        const params = { limit };
        if (entityType) params.entity_type = entityType;
        const query = new URLSearchParams(params).toString();
        return request(`/history?${query}`);
    }
};

// ============== BIA API ==============
export const bia = {
    async getSettings() {
        return request('/bia/settings');
    },
    async updateSettings(data) {
        return request('/bia/settings', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    async getProcesses() {
        return request('/bia/processes');
    },
    async createProcess(data) {
        return request('/bia/processes', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async updateProcess(id, data) {
        return request(`/bia/processes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    async deleteProcess(id) {
        return request(`/bia/processes/${id}`, {
            method: 'DELETE'
        });
    },
    async createAsset(data) {
        return request('/bia/assets', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async updateAsset(id, data) {
        return request(`/bia/assets/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    async deleteAsset(id) {
        return request(`/bia/assets/${id}`, {
            method: 'DELETE'
        });
    },
    async getComplianceLevel() {
        return request('/bia/compliance-level');
    }
};

export default {
    auth,
    organization,
    controls,
    evaluations,
    dashboard,
    history,
    bia,
    getToken,
    getUser,
    isAuthenticated
};
