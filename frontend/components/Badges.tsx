import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL, type TicketPriority, type TicketStatus, type TicketCategory } from "@/lib/types";

const STATUS_CLASS: Record<TicketStatus, string> = {
  open: "bg-amber-100 text-amber-900",
  in_progress: "bg-sky-100 text-sky-900",
  resolved: "bg-emerald-100 text-emerald-900",
  closed: "bg-stone-200 text-stone-700",
};

const PRIORITY_CLASS: Record<TicketPriority, string> = {
  critical: "bg-red-100 text-red-900",
  high: "bg-orange-100 text-orange-900",
  medium: "bg-amber-50 text-amber-800",
  low: "bg-stone-100 text-stone-600",
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[status]}`}>{STATUS_LABEL[status]}</span>;
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_CLASS[priority]}`}>{PRIORITY_LABEL[priority]}</span>;
}

export function CategoryBadge({ category }: { category: TicketCategory }) {
  return <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-700">{CATEGORY_LABEL[category]}</span>;
}
