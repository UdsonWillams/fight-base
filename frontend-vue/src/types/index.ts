export interface Fighter {
  id: string
  name: string
  nickname: string | null
  last_organization_fight: string | null
  actual_weight_class: string | null
  stance: string | null
  gender: string | null
  height_cm: number | null
  weight: number | null
  reach_cm: number | null
  wins: number
  losses: number
  draws: number
  overall_rating: number
  striking: number
  grappling: number
  defense: number
  stamina: number
  speed: number
  strategy: number
  fighting_style: string | null
  is_real: boolean
  record: string | null
  cartel: string | null
  slpm: number | null
  str_acc: number | null
  sapm: number | null
  str_def: number | null
  td_avg: number | null
  td_acc: number | null
  td_def: number | null
  sub_avg: number | null
  image_url: string | null
  creator_id: string | null
  created_at: string
  updated_at: string
}

export interface FighterListResponse {
  fighters: Fighter[]
  total: number
  limit: number
  offset: number
}

export interface FighterCreate {
  name: string
  last_organization_fight: string
  actual_weight_class: string
  fighting_style: string
  nickname?: string
  stance?: string
  gender?: string
  height_cm?: number
  weight?: number
  reach_cm?: number
  wins?: number
  losses?: number
  draws?: number
  overall_rating?: number
  striking?: number
  grappling?: number
  defense?: number
  stamina?: number
  speed?: number
  strategy?: number
  is_real?: boolean
  record?: string
  cartel?: string
  slpm?: number
  str_acc?: number
  sapm?: number
  str_def?: number
  td_avg?: number
  td_acc?: number
  td_def?: number
  sub_avg?: number
}

export interface FighterStats {
  total_fighters: number
  last_organizations: Record<string, number>
  weight_classes: Record<string, number>
  avg_overall_rating: number
  total_real: number
  total_fictional: number
}

export interface FighterSummary {
  id: string
  name: string
  nickname: string | null
  actual_weight_class: string | null
  image_url: string | null
  overall_rating: number | null
  record: string | null
}

export interface Event {
  id: string
  name: string
  date: string
  location: string | null
  organization: string | null
  status: string
  poster_url: string | null
  fights_count: number
  created_at: string
}

export interface EventDetail extends Event {
  description: string | null
  updated_at: string
  fights: Fight[]
}

export interface Fight {
  id: string
  event_id: string
  fighter1_id: string
  fighter2_id: string
  fighter1: FighterSummary | null
  fighter2: FighterSummary | null
  fight_order: number
  fight_type: string
  weight_class: string | null
  rounds: number
  is_title_fight: boolean
  status: string
  winner_id: string | null
  winner: FighterSummary | null
  result_type: string | null
  finish_round: number | null
  finish_time: string | null
  method_details: string | null
  fighter1_probability: number | null
  fighter2_probability: number | null
  simulation_details: any | null
  created_at: string
  updated_at: string
}

export interface FightCreate {
  fighter1_id: string
  fighter2_id: string
  fight_order?: number
  fight_type?: string
  weight_class?: string
  rounds?: number
  is_title_fight?: boolean
}

export interface Simulation {
  id: string
  fighter1_id: string
  fighter1_name: string
  fighter2_id: string
  fighter2_name: string
  rounds: number
  result_type: string
  winner_id: string
  winner_name: string
  method_details: string
  finish_round: number
  finish_time: string
  round_details: RoundDetail[]
  fighter1_probability: number
  fighter2_probability: number
  created_at: string
}

export interface SimulationResult {
  result_type: string
  winner_id: string
  winner_name: string
  fighter1_id?: string
  fighter1_name?: string
  fighter2_id?: string
  fighter2_name?: string
  finish_round: number | null
  finish_time: string | null
  method_details: string | null
  fighter1_probability: number
  fighter2_probability: number
  simulation_details: any | null
}

export interface RoundDetail {
  round_number: number
  events: string[]
}

export interface SimulationStats {
  total_simulations: number
  by_result_type: Record<string, number>
  avg_rounds: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  name: string
  avatar: string | null
  role: string
  created_at: string
}

export interface Prediction {
  id: string
  user_id: string
  fight_id: string
  event_id: string
  predicted_winner_id: string | null
  predicted_method_id: string | null
  predicted_round: number | null
  is_winner_correct: boolean | null
  is_method_correct: boolean | null
  is_round_correct: boolean | null
  points_earned: number
  processed_at: string | null
}

export interface LeaderboardEntry {
  user_id: string
  username: string
  total_points: number
  correct_winners: number
  rank: number | null
}

export interface UserPredictionStats {
  total_points: number
  total_predictions: number
  correct_winners: number
  underdog_bonus_points: number
  global_rank: number | null
  current_streak: number
  best_streak: number
  events_participated: number
}

export interface Achievement {
  code: string
  name: string
  description: string
  icon: string | null
  unlocked_at: string | null
}

export interface League {
  id: string
  name: string
  description: string | null
  invite_code: string
  members_count: number
  owner_id: string
  active_event_id?: string | null
  active_event_name?: string | null
  created_at: string
}

export interface LeagueDetail {
  id: string
  name: string
  description: string | null
  invite_code: string
  owner_id: string
  owner_name: string
  members_count: number
  is_owner: boolean
  is_member: boolean
  active_event_id: string | null
  active_event_name: string | null
  active_event_date: string | null
  active_event_fights_count: number
}

export interface LeagueLeaderboardEntry {
  user_id: string
  username: string
  total_points: number
  rank: number | null
}

export interface LeaguePrediction {
  id: string
  fight_id: string
  fighter1_name: string | null
  fighter2_name: string | null
  predicted_winner_id: string | null
  predicted_winner_name: string | null
  is_correct: boolean | null
  points_earned: number
}
