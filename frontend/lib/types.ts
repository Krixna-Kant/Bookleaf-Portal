export type Role = "author" | "admin";

export type User = {
  id: number;
  email: string;
  name: string;
  role: Role;
  external_author_id: string | null;
  phone: string | null;
  city: string | null;
  joined_date: string | null;
};

export type Book = {
  id: number;
  external_book_id: string;
  title: string;
  isbn: string | null;
  genre: string | null;
  publication_date: string | null;
  status: string;
  mrp: string | null;
  author_royalty_per_copy: string | null;
  total_copies_sold: number;
  total_royalty_earned: string;
  royalty_paid: string;
  royalty_pending: string;
  last_royalty_payout_date: string | null;
  print_partner: string | null;
  available_on: string[];
  in_production: boolean;
  below_payout_threshold: boolean;
};

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketCategory =
  | "royalty_payments"
  | "isbn_metadata"
  | "printing_quality"
  | "distribution"
  | "book_status"
  | "general";
export type TicketPriority = "critical" | "high" | "medium" | "low";

export type TicketSummary = {
  id: number;
  ticket_number: string;
  subject: string;
  status: TicketStatus;
  category: TicketCategory;
  category_source: "ai" | "admin" | "rule";
  priority: TicketPriority;
  priority_source: "ai" | "admin" | "rule";
  priority_score: number;
  book_id: number | null;
  book_title: string | null;
  author_id: number;
  author_name: string;
  assigned_to_id: number | null;
  assigned_to_name: string | null;
  ai_draft_status: "pending" | "ready" | "failed" | "sent";
  created_at: string;
  updated_at: string;
  aging_hours: number;
};

export type TicketMessage = {
  id: number;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  body: string;
  created_at: string;
};

export type TicketNote = {
  id: number;
  admin_id: number;
  admin_name: string;
  body: string;
  created_at: string;
};

export type TicketDetail = TicketSummary & {
  description: string;
  ai_draft: string | null;
  ai_rationale: string | null;
  ai_confidence: number | null;
  book: Book | null;
  author: User | null;
  messages: TicketMessage[];
  notes: TicketNote[];
};

export type AdminStats = {
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
  critical: number;
  high: number;
  aging_over_48h: number;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export const CATEGORY_LABEL: Record<TicketCategory, string> = {
  royalty_payments: "Royalty & Payments",
  isbn_metadata: "ISBN & Metadata",
  printing_quality: "Printing & Quality",
  distribution: "Distribution",
  book_status: "Production",
  general: "General",
};

export const STATUS_LABEL: Record<TicketStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  resolved: "Resolved",
  closed: "Closed",
};

export const PRIORITY_LABEL: Record<TicketPriority, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};
