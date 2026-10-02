export type AdminUserStatus = "active" | "suspended" | "deleted";
export type AdminEntitlementStatus = "none" | "trial" | "active" | "expired" | "cancelled";
export type AdminPlanCode = "free" | "pro";

export type AdminOverview = {
  total_users: number;
  active_trials: number;
  paid_users: number;
  expired_entitlements: number;
  ai_requests: number;
  registrations_7d: number;
  finance_accounts: number;
  transactions: number;
  assets: number;
  liabilities: number;
  security_events_24h: number;
  unverified_users: number;
};

export type AdminAnalyticsOverview = {
  total_users: number;
  active_users: number;
  new_users_today: number;
  new_users_7d: number;
  new_users_30d: number;
  active_trials: number;
  paid_users: number;
  free_users: number;
  expired_users: number;
  suspended_users: number;
  revenue_today: number | string;
  revenue_this_month: number | string;
  revenue_this_year: number | string;
  total_recorded_revenue: number | string;
  ai_requests_today: number;
  ai_requests_7d: number;
  security_events_24h: number;
  failed_login_attempts: number;
  unverified_emails: number;
  finance_accounts: number;
  transactions: number;
};

export type UserGrowthPoint = {
  date: string;
  registrations: number;
  cumulative: number;
};

export type AdminAnalyticsUsers = {
  period: string;
  points: UserGrowthPoint[];
  total_registrations: number;
};

export type RevenuePoint = {
  date: string;
  revenue: number | string;
  count: number;
  voided_amount: number | string;
};

export type AdminAnalyticsRevenue = {
  period: string;
  points: RevenuePoint[];
  total_revenue: number | string;
  total_transactions: number;
  voided_revenue: number | string;
};

export type PlanDistributionItem = {
  plan_code: string;
  count: number;
  percentage: number;
};

export type TrialConversionMetrics = {
  trials_started: number;
  trials_active: number;
  trials_converted: number;
  trials_expired: number;
  conversion_rate_pct: number;
};

export type PaymentMethodDistributionItem = {
  method: string;
  count: number;
  amount: number | string;
  percentage: number;
};

export type AdminAnalyticsSubscriptions = {
  distribution: {
    trial: number;
    free: number;
    active_paid: number;
    expired: number;
    cancelled: number;
    suspended: number;
  };
  by_plan: PlanDistributionItem[];
  trial_conversion: TrialConversionMetrics;
  payment_methods: PaymentMethodDistributionItem[];
};

export type AIUsagePoint = {
  date: string;
  requests: number;
  prompt_chars: number;
  response_chars: number;
};

export type AITopUser = {
  user_id: string;
  user_email: string;
  requests: number;
};

export type AdminAnalyticsAI = {
  total_requests: number;
  requests_24h: number;
  requests_7d: number;
  requests_30d: number;
  unique_users_7d: number;
  points: AIUsagePoint[];
  top_users: AITopUser[];
};

export type SecurityTrendPoint = {
  date: string;
  total: number;
  logins: number;
  failures: number;
};

export type SecurityBreakdownItem = {
  event_type: string;
  count: number;
};

export type AdminAnalyticsSecurity = {
  period: string;
  total_events: number;
  failed_logins: number;
  breakdown: SecurityBreakdownItem[];
  points: SecurityTrendPoint[];
};

export type AdminPaginationMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type AdminUserRow = {
  id: string;
  email: string;
  full_name: string | null;
  user_status: string;
  is_admin: boolean;
  email_verified: boolean;
  entitlement_status: string | null;
  plan_code: string | null;
  billing_plan_id: string | null;
  billing_plan_name?: string | null;
  trial_ends_at: string | null;
  paid_until: string | null;
  created_at: string;
};

export type AdminPaginatedUsers = {
  items: AdminUserRow[];
  meta: AdminPaginationMeta;
};

export type AdminBillingPlanRow = {
  id: string;
  code: string;
  name: string;
  access_level: "free" | "pro";
  billing_period: "monthly" | "quarterly" | "yearly" | "lifetime";
  google_play_product_id: string | null;
  price: number | string;
  currency: string;
  description: string | null;
  features: Record<string, unknown> | null;
  is_active: boolean;
  active_subscribers_count: number;
  created_at: string;
  updated_at: string;
};

export type AdminPaymentRow = {
  id: string;
  user_id: string;
  user_email: string;
  billing_plan_id: string | null;
  billing_plan_name: string | null;
  amount: number | string;
  currency: string;
  payment_method: string;
  provider: string | null;
  reference: string | null;
  status: "received" | "pending" | "refunded" | "failed" | "voided";
  notes: string | null;
  received_at: string;
  recorded_by_admin_email: string | null;
  created_at: string;
};

export type AdminPaginatedPayments = {
  items: AdminPaymentRow[];
  meta: AdminPaginationMeta;
};

export type AdminSecurityEventRow = {
  id: string;
  user_id: string | null;
  user_email: string | null;
  event_type: string;
  description: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export type AdminPaginatedSecurityEvents = {
  items: AdminSecurityEventRow[];
  meta: AdminPaginationMeta;
};

export type AdminActionLogRow = {
  id: string;
  actor_admin_id: string | null;
  actor_admin_email: string | null;
  target_user_id: string | null;
  target_user_email: string | null;
  action: string;
  reason: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export type AdminPaginatedActionLogs = {
  items: AdminActionLogRow[];
  meta: AdminPaginationMeta;
};

export type AdminUserFinancialSummary = {
  accounts_count: number;
  transactions_count: number;
  assets_count: number;
  liabilities_count: number;
  last_activity_date: string | null;
};

export type AdminUserDetail = {
  user: AdminUserRow;
  country: string | null;
  state: string | null;
  city: string | null;
  postal_code: string | null;
  last_ip_address: string | null;
  last_user_agent: string | null;
  location_updated_at: string | null;
  payments: AdminPaymentRow[];
  financial_summary: AdminUserFinancialSummary;
  recent_security_events: AdminSecurityEventRow[];
  recent_admin_actions: AdminActionLogRow[];
  active_sessions_count: number;
};

export type Readiness = {
  status: string;
  database: string;
  environment: string;
  email_delivery: string;
  email_mode: string;
  google_play: string;
  ai: string;
  cors: string;
  production_release: string;
};

export type AppRelease = {
  latest_version: string;
  latest_build_number: number;
  minimum_version: string;
  minimum_build_number: number;
  update_url: string | null;
  release_notes: string | null;
  distribution: "apk" | "play_store";
  is_update_enabled: boolean;
  updated_at: string;
};
