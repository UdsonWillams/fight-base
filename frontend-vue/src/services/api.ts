import type {
  Fighter,
  FighterCreate,
  Event,
  EventDetail,
  Fight,
  Simulation,
  SimulationResult,
  User,
  LoginResponse,
  Prediction,
  League,
  Achievement,
  FighterStats,
  SimulationStats,
  FightCreate,
  FighterListResponse,
  LeaderboardEntry,
  UserPredictionStats,
} from '@/types'

const API_BASE_URL = 'https://fightbase-api.onrender.com/api/v1'

class ApiClient {
  private baseURL: string
  private token: string | null

  constructor() {
    this.baseURL = API_BASE_URL
    this.token = localStorage.getItem('idToken')
  }

  setToken(token: string | null): void {
    this.token = token
    if (token) {
      localStorage.setItem('idToken', token)
    } else {
      localStorage.removeItem('idToken')
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    return headers
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...((options.headers as Record<string, string>) || {}),
      },
    }
    const response = await fetch(url, config)
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || 'Request failed')
    }
    if (response.status === 204) {
      return null as T
    }
    return response.json()
  }

  // ── Auth ──

  async register(data: {
    email: string
    password: string
    username: string
    avatar?: string
    birth_date?: string
  }): Promise<User> {
    return this.request('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    return this.request('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async getCurrentUser(): Promise<User | null> {
    if (!this.token) return null
    try {
      const payload = JSON.parse(atob(this.token.split('.')[1]))
      return this.request(`/users/email/${encodeURIComponent(payload.sub)}`)
    } catch {
      return null
    }
  }

  async getUser(userId: string): Promise<User> {
    return this.request(`/users/${userId}`)
  }

  async updateUser(userId: string, data: Partial<User>): Promise<User> {
    return this.request(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // ── Fighters ──

  async getFighters(params: Record<string, string | number> = {}): Promise<FighterListResponse> {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString()
    return this.request(`/fighters/${q ? '?' + q : ''}`)
  }

  async getFighter(id: string): Promise<Fighter> {
    return this.request(`/fighters/${id}`)
  }

  async createFighter(data: FighterCreate): Promise<Fighter> {
    return this.request('/fighters/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateFighter(id: string, data: Partial<FighterCreate>): Promise<Fighter> {
    return this.request(`/fighters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteFighter(id: string): Promise<void> {
    return this.request(`/fighters/${id}`, { method: 'DELETE' })
  }

  async getTopFighters(params: Record<string, string | number> = {}): Promise<FighterListResponse> {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString()
    return this.request(`/fighters/rankings/top/${q ? '?' + q : ''}`)
  }

  async getFighterStats(): Promise<FighterStats> {
    return this.request('/fighters/statistics/overview')
  }

  async getMyFighters(): Promise<Fighter[]> {
    return this.request('/fighters/my/fighters')
  }

  // ── Photos ──

  async uploadFighterPhoto(fighterId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${this.baseURL}/fighters/${fighterId}/photo`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
      body: formData,
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || 'Upload failed')
    }
    return res.json()
  }

  async deleteFighterPhoto(fighterId: string): Promise<void> {
    return this.request(`/fighters/${fighterId}/photo`, { method: 'DELETE' })
  }

  async listFighterPhotos(fighterId: string): Promise<any[]> {
    return this.request(`/fighters/${fighterId}/photos`)
  }

  // ── Simulations ──

  async createSimulation(data: {
    fighter1_id: string
    fighter2_id: string
    rounds: number
  }): Promise<SimulationResult> {
    return this.request('/simulations/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async predictFight(fighter1_id: string, fighter2_id: string): Promise<any> {
    return this.request(
      `/simulations/predict?fighter1_id=${fighter1_id}&fighter2_id=${fighter2_id}`
    )
  }

  async compareFighters(fighter1_id: string, fighter2_id: string): Promise<any> {
    return this.request(
      `/simulations/compare?fighter1_id=${fighter1_id}&fighter2_id=${fighter2_id}`
    )
  }

  async getFighterHistory(fighter_id: string, limit = 20): Promise<Simulation[]> {
    return this.request(`/simulations/history/${fighter_id}?limit=${limit}`)
  }

  async getMatchupHistory(fighter1_id: string, fighter2_id: string): Promise<Simulation[]> {
    return this.request(
      `/simulations/matchup?fighter1_id=${fighter1_id}&fighter2_id=${fighter2_id}`
    )
  }

  async getRecentSimulations(limit = 10): Promise<Simulation[]> {
    return this.request(`/simulations/recent?limit=${limit}`)
  }

  async getSimulationStats(): Promise<SimulationStats> {
    return this.request('/simulations/statistics/overview')
  }

  // ── Events ──

  async createEvent(data: {
    name: string
    date: string
    location?: string
    organization?: string
    fights?: FightCreate[]
  }): Promise<Event> {
    return this.request('/events/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getEvents(params: Record<string, string | number> = {}): Promise<Event[]> {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString()
    return this.request(`/events/${q ? '?' + q : ''}`)
  }

  async getEvent(eventId: string): Promise<EventDetail> {
    return this.request(`/events/${eventId}`)
  }

  async addFightToEvent(eventId: string, fightData: FightCreate): Promise<Fight> {
    return this.request(`/events/${eventId}/fights`, {
      method: 'POST',
      body: JSON.stringify(fightData),
    })
  }

  async simulateEvent(eventId: string): Promise<any> {
    return this.request(`/events/${eventId}/simulate`, { method: 'POST' })
  }

  async updateFightResult(
    eventId: string,
    fightId: string,
    data: { winner_id: string; method_details: string; finish_round: number; finish_time: string }
  ): Promise<any> {
    return this.request(`/events/${eventId}/fights/${fightId}/result`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteEvent(eventId: string): Promise<void> {
    return this.request(`/events/${eventId}`, { method: 'DELETE' })
  }

  async updateEvent(eventId: string, data: Record<string, unknown>): Promise<EventDetail> {
    return this.request(`/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // ── Predictions ──

  async createPrediction(data: {
    fight_id: string
    predicted_winner_id: string
    predicted_method?: string
    predicted_round?: number
  }): Promise<Prediction> {
    return this.request('/predictions/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getMyPredictions(eventId: string): Promise<Prediction[]> {
    return this.request(`/predictions/my/event/${eventId}`)
  }

  async getEventLeaderboard(eventId: string, limit = 50): Promise<LeaderboardEntry[]> {
    return this.request(`/predictions/leaderboard/event/${eventId}?limit=${limit}`)
  }

  async getUserStats(): Promise<UserPredictionStats> {
    return this.request('/predictions/my/stats')
  }

  async getAchievements(): Promise<Achievement[]> {
    return this.request('/predictions/my/achievements')
  }

  async getFinishMethods(): Promise<any[]> {
    return this.request('/predictions/finish-methods')
  }

  // ── Leagues ──

  async createLeague(data: { name: string; description?: string }): Promise<League> {
    return this.request('/leagues/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async joinLeague(inviteCode: string): Promise<any> {
    return this.request(`/leagues/join/${inviteCode}`, { method: 'POST' })
  }

  async getMyLeagues(): Promise<League[]> {
    return this.request('/leagues/my')
  }
}

export const api = new ApiClient()

export const authApi = {
  login: (email: string, password: string) => api.login(email, password),
  register: (data: { email: string; password: string; name?: string; username?: string }) =>
    api.register({ email: data.email, password: data.password, username: data.username || data.name || '' }),
}

export const fightersApi = {
  async search(params: { name?: string; limit?: number }) {
    const fighters = await api.getFighters({ name: params.name || '', limit: String(params.limit || 10) })
    return { fighters }
  },
  getById: (id: string) => api.getFighter(id),
}
