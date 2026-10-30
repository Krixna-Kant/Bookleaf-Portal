import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL, type TicketCategory, type TicketPriority, type TicketStatus } from "@/lib/types";

export function StatusBadge({ status, sketch = false }: { status: TicketStatus; sketch?: boolean }) {
  const label = STATUS_LABEL[status];
  if (sketch) {
    const wash = status === "open" ? "crayon-sage" : status === "in_progress" ? "crayon-ochre" : "bg-[#f2ede2]";
    return <span className={`inline-flex rounded-full border border-[#2b2a27] px-2 py-0.5 font-note text-[11px] font-bold ${wash}`}>{label}</span>;
  }
  const tone =
    status === "open"
      ? "bg-[#c5edc1] text-[#07290c]"
      : status === "in_progress"
        ? "bg-[#ffdeaa] text-[#271900]"
        : "bg-[#e5e2de] text-[#424840]";
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${tone}`}>{label}</span>;
}

export function PriorityBadge({ priority, sketch = false }: { priority: TicketPriority; sketch?: boolean }) {
  const label = PRIORITY_LABEL[priority];
  if (sketch) {
    const wash = priority === "critical" || priority === "high" ? "crayon-peach" : priority === "medium" ? "crayon-ochre" : "bg-[#f2ede2]";
    return <span className={`inline-flex rounded-full border border-[#2b2a27] px-2 py-0.5 font-note text-[11px] font-bold ${wash}`}>{label}</span>;
  }
  const tone =
    priority === "critical"
      ? "bg-[#ffdad6] text-[#93000a]"
      : priority === "high"
        ? "bg-[#fdc662] text-[#271900]"
        : "bg-[#f0edea] text-[#424840]";
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${tone}`}>{label}</span>;
}

export function CategoryBadge({ category, sketch = false }: { category: TicketCategory; sketch?: boolean }) {
  const label = CATEGORY_LABEL[category];
  if (sketch) {
    return <span className="font-hand text-base text-[#825c18]">{label}</span>;
  }
  return <span className="rounded-full bg-[#f0edea] px-2 py-0.5 text-[11px] text-[#424840]">{label}</span>;
}
