export interface Project {
  id: string;
  name: string;
  repo: string;
  url: string;
  category: string;
  tagline: string;
  summary: string;
  highlights: string[];
  technologies: string[];
  stars?: number;
}

export interface Milestone {
  id: string;
  category: string;
  title: string;
  role: string;
  summary: string;
  impact_metrics: string[];
  technologies: string[];
}

export interface SkillItem {
  name: string;
  proficiency: 'Expert' | 'Proficient' | 'Familiar';
  context: string;
}

export interface SkillCategory {
  name: string;
  skills: SkillItem[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sources?: {
    id: string;
    title: string;
    category: string;
    excerpt: string;
    rrf_score?: number;
  }[];
}

export interface QuotaStatus {
  authenticated: boolean;
  tier: 'anonymous' | 'authenticated';
  limit: number;
  remaining: number;
  reset_seconds: number;
  user_email?: string;
  user_name?: string;
}

export interface ContactSubmission {
  name?: string;
  email: string;
  question: string;
}
