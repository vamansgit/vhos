export type BrandStage = "idea" | "pre_launch" | "live";
export type BusinessStructure = "not_incorporated" | "proprietorship" | "llp" | "pvt_ltd";
export type ModuleName = "onboard" | "source" | "sell" | "finance" | "none";
export type ChatRole = "user" | "assistant";

export interface User {
  id: string;
  brand_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface Brand {
  id: string;
  name: string;
  category: string | null;
  stage: BrandStage;
  structure: BusinessStructure;
  target_geographies: string | null;
  style_descriptors: string | null;
  team_size: number;
}

export interface FounderProfile {
  background_text: string | null;
  skills: string | null;
  aspirations_text: string | null;
  risk_appetite: string | null;
  time_availability_hours_per_week: number | null;
}

export interface DocumentVersion {
  id: string;
  version_number: number;
  file_ref: string;
  note: string | null;
  created_at: string;
}

export interface DocumentOut {
  id: string;
  type: string;
  label: string;
  status: string;
  current_file_ref: string | null;
  expiry_date: string | null;
  extracted_value: string | null;
  versions: DocumentVersion[];
}

export interface ChecklistItem {
  id: string;
  requirement: string;
  due_context: string | null;
  status: "not_started" | "in_progress" | "done" | "not_applicable";
}

// --- Source ---

export interface SourcingRequest {
  id: string;
  brand_id: string;
  raw_text: string;
  category: string;
  parsed_spec: Record<string, unknown>;
  quantity: number | null;
  target_price: number | null;
  destination: string | null;
  deadline: string | null;
  status: string;
  confirmation_line?: string | null;
}

export interface Supplier {
  id: string;
  name: string;
  source_network: string;
  supplier_type: string;
  category_tags: string;
  verification_status: string;
  rating: number;
  lead_time_avg_days: number;
  location: string | null;
}

export interface CatalogItem {
  id: string;
  title: string;
  spec_attributes: Record<string, unknown>;
  price_breaks: { min_qty: number; unit_price: number }[];
  moq: number;
}

export interface SourcingMatch {
  id: string;
  supplier: Supplier;
  catalog_item: CatalogItem;
  fit_score: number;
  estimated_unit_price: number;
  reason: string;
  rank: number;
}

export interface RFQ {
  id: string;
  supplier: Supplier;
  message: string;
  status: string;
  quote: Quote | null;
}

export interface Quote {
  id: string;
  unit_price: number;
  moq: number;
  lead_time_days: number;
  terms: string | null;
}

export interface SourcedOrder {
  id: string;
  title: string;
  category: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  status: string;
}

// --- Sell ---

export interface Store {
  id: string;
  domain: string;
  theme_config: { palette?: Record<string, string>; tagline?: string; style_label?: string };
  pages: { slug: string; title: string }[];
  published: boolean;
}

export interface Product {
  id: string;
  sourced_order_id: string | null;
  title: string;
  price: number;
  cost_basis: number;
  inventory: number;
}

export interface ShippingZone {
  id: string;
  region: string;
  carrier: string;
  rate_rules: Record<string, unknown>;
}

export interface PaymentProvider {
  id: string;
  provider: "razorpay" | "stripe" | "payu" | "upi";
  status: "pre_enabled" | "active" | "disabled";
  kyc_status: "not_started" | "pending" | "complete";
}

export interface StoreOrder {
  id: string;
  line_items: { product_id: string; title: string; qty: number; unit_price: number }[];
  subtotal: number;
  fulfillment_status: string;
  created_at: string;
}

export interface HelpContentItem {
  id: string;
  module: string;
  topic: string;
  type: string;
  body: string;
  category_tags: string | null;
}

// --- Finance ---

export interface FinanceDashboard {
  revenue: number;
  cogs: number;
  expenses: number;
  ad_spend: number;
  gross_profit: number;
  gross_margin_pct: number | null;
  net_profit: number;
  cash_position: number;
  daily_series: { date: string; revenue: number; cogs: number; expenses: number; ad_spend: number }[];
}

export interface TaxProfile {
  gstin: string | null;
  state: string | null;
  applicable_schemes: string | null;
}

// --- Chat ---

export interface ChatMessageOut {
  id: string;
  role: ChatRole;
  module: ModuleName;
  content: string;
  structured_payload: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatSendResponse {
  reply: string;
  module: ModuleName;
  payload: Record<string, unknown>;
}
