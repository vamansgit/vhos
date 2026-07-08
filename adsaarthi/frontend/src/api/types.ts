export type UserRole = "owner" | "marketer" | "content_manager";
export type AdPlatform = "meta" | "youtube" | "google_ads";
export type AdAccountStatus = "pending" | "connected" | "error" | "disconnected";
export type CampaignObjective = "awareness" | "launch" | "sales" | "retargeting" | "influencer_collab";
export type ContentFormat = "reels" | "youtube_shorts" | "youtube_long_form" | "static_post";
export type CampaignBriefStatus = "draft" | "matching" | "matched" | "launched" | "completed";
export type MatchStatus = "pending_review" | "approved" | "rejected" | "adjusted";
export type ContentDraftType = "blog" | "ad_copy" | "creator_brief" | "image";
export type ContentDraftStatus = "draft" | "approved" | "published" | "rejected";
export type InfluencerCategory =
  | "beauty"
  | "fashion"
  | "wellness"
  | "food"
  | "tech"
  | "home"
  | "fitness"
  | "parenting"
  | "finance"
  | "travel";

export interface User {
  id: string;
  brand_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Brand {
  id: string;
  name: string;
  category: string | null;
  target_audience: string | null;
  brand_voice: string | null;
  cac_alert_threshold_pct: number;
}

export interface AdAccount {
  id: string;
  platform: AdPlatform;
  display_name: string;
  external_account_id: string;
  status: AdAccountStatus;
  last_synced_at: string | null;
}

export interface DailyPoint {
  date: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  cac: number | null;
  roas: number | null;
}

export interface PlatformBreakdown {
  platform: string;
  spend: number;
  conversions: number;
  cac: number | null;
  roas: number | null;
}

export interface CampaignBreakdown {
  campaign_name: string;
  platform: string;
  spend: number;
  conversions: number;
  cac: number | null;
  roas: number | null;
}

export interface TrendAlert {
  triggered: boolean;
  current_cac: number | null;
  previous_cac: number | null;
  change_pct: number | null;
  threshold_pct: number;
  message: string;
}

export interface CategoryBenchmark {
  category: string;
  avg_cac: number;
  avg_roas: number;
  brand_cac: number | null;
  brand_roas: number | null;
}

export interface DashboardSummary {
  total_spend: number;
  total_conversions: number;
  total_revenue: number;
  blended_cac: number | null;
  blended_roas: number | null;
  daily_series: DailyPoint[];
  by_platform: PlatformBreakdown[];
  by_campaign: CampaignBreakdown[];
  trend_alert: TrendAlert;
  benchmark: CategoryBenchmark | null;
}

export interface Influencer {
  id: string;
  handle: string;
  display_name: string;
  platform: AdPlatform;
  category: InfluencerCategory;
  follower_count: number;
  engagement_rate_pct: number;
  posting_consistency_score: number;
  audience_age_range: string | null;
  audience_geography: string | null;
  audience_interests: string | null;
  indicative_price_min: number;
  indicative_price_max: number;
  top_content_style: string | null;
  historical_avg_engagement_pct: number;
  historical_campaigns_count: number;
}

export interface CampaignBrief {
  id: string;
  brand_id: string;
  objective: CampaignObjective;
  target_audience_age: string | null;
  target_audience_gender: string | null;
  target_audience_geography: string | null;
  target_audience_interests: string | null;
  desired_reach: number | null;
  content_format: ContentFormat;
  total_budget: number;
  status: CampaignBriefStatus;
  notes: string | null;
}

export interface MatchResult {
  id: string;
  campaign_brief_id: string;
  influencer: Influencer;
  fit_score: number;
  engagement_quality_score: number;
  audience_overlap_score: number;
  consistency_score: number;
  reason: string;
  recommended_bid: number;
  projected_reach: number;
  tier: string;
  status: MatchStatus;
  approved_bid: number | null;
  rank: number;
}

export interface ContentDraft {
  id: string;
  brand_id: string;
  match_result_id: string | null;
  type: ContentDraftType;
  title: string;
  body: string;
  topic: string | null;
  platform_variant: string | null;
  status: ContentDraftStatus;
  scheduled_date: string | null;
  generated_by: string;
  created_at: string;
}

export interface BudgetRecommendation {
  id: string;
  trend: "improving" | "worsening" | "stable";
  message: string;
  suggested_paid_pct: number;
  suggested_influencer_pct: number;
  suggested_content_pct: number;
}
