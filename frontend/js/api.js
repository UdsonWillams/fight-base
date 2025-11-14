// API Configuration
const API_BASE_URL = "http://localhost:8080/api/v1";

// API Client
class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem("idToken");
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem("idToken", token);
        } else {
            localStorage.removeItem("idToken");
        }
    }

    getHeaders() {
        const headers = {
            "Content-Type": "application/json",
        };

        if (this.token) {
            headers["Authorization"] = `Bearer ${this.token}`;
        }

        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Request failed");
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error("API Error:", error);
            throw error;
        }
    }

    // Auth & Users
    async register(data) {
        return this.request("/users", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async login(email, password) {
        return this.request("/auth/token", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
    }

    async getCurrentUser() {
        // Decode JWT token to get user email
        if (!this.token) return null;

        try {
            const payload = JSON.parse(atob(this.token.split(".")[1]));
            const email = payload.sub;
            return this.request(`/users/email/${encodeURIComponent(email)}`);
        } catch (error) {
            console.error("Error getting current user:", error);
            return null;
        }
    }

    async getUser(userId) {
        return this.request(`/users/${userId}`);
    }

    async updateUser(userId, data) {
        return this.request(`/users/${userId}`, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }

    // Fighters
    async getFighters(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/fighters/${query ? "?" + query : ""}`);
    }

    async getFighter(id) {
        return this.request(`/fighters/${id}`);
    }

    async getFighterById(id) {
        return this.getFighter(id);
    }

    async createFighter(data) {
        return this.request("/fighters/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async updateFighter(id, data) {
        return this.request(`/fighters/${id}`, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }

    async deleteFighter(id) {
        return this.request(`/fighters/${id}`, {
            method: "DELETE",
        });
    }

    async getTopFighters(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(
            `/fighters/rankings/top/${query ? "?" + query : ""}`
        );
    }

    async getFighterStats() {
        return this.request("/fighters/statistics/overview");
    }

    // Simulations
    async createSimulation(data) {
        return this.request("/simulations/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async predictFight(fighter1_id, fighter2_id) {
        const query = new URLSearchParams({
            fighter1_id,
            fighter2_id,
        }).toString();
        return this.request(`/simulations/predict?${query}`);
    }

    async compareFighters(fighter1_id, fighter2_id) {
        const query = new URLSearchParams({
            fighter1_id,
            fighter2_id,
        }).toString();
        return this.request(`/simulations/compare?${query}`);
    }

    async getFighterHistory(fighter_id, limit = 20) {
        const query = new URLSearchParams({ limit }).toString();
        return this.request(`/simulations/history/${fighter_id}?${query}`);
    }

    async getMatchupHistory(fighter1_id, fighter2_id) {
        const query = new URLSearchParams({
            fighter1_id,
            fighter2_id,
        }).toString();
        return this.request(`/simulations/matchup?${query}`);
    }

    async getRecentSimulations(limit = 10) {
        const query = new URLSearchParams({ limit }).toString();
        return this.request(`/simulations/recent?${query}`);
    }

    async getSimulationStats() {
        return this.request("/simulations/statistics/overview");
    }

    // Events
    async createEvent(data) {
        return this.request("/events/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async getEvents(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/events/${query ? "?" + query : ""}`);
    }

    async getEvent(eventId) {
        return this.request(`/events/${eventId}`);
    }

    async updateEvent(eventId, data) {
        return this.request(`/events/${eventId}`, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }

    async addFightToEvent(eventId, fightData) {
        return this.request(`/events/${eventId}/fights`, {
            method: "POST",
            body: JSON.stringify(fightData),
        });
    }

    async simulateEvent(eventId) {
        return this.request(`/events/${eventId}/simulate`, {
            method: "POST",
        });
    }

    async deleteEvent(eventId) {
        return this.request(`/events/${eventId}`, {
            method: "DELETE",
        });
    }

    // Photos
    async uploadFighterPhoto(fighterId, file) {
        const formData = new FormData();
        formData.append("file", file);

        return fetch(`${this.baseURL}/fighters/${fighterId}/photo`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${this.token}`,
            },
            body: formData,
        }).then((res) => {
            if (!res.ok) throw new Error("Upload failed");
            return res.json();
        });
    }

    async deleteFighterPhoto(fighterId) {
        return this.request(`/fighters/${fighterId}/photo`, {
            method: "DELETE",
        });
    }

    async listFighterPhotos(fighterId) {
        return this.request(`/fighters/${fighterId}/photos`);
    }
}

// Export global instance
const api = new APIClient();
