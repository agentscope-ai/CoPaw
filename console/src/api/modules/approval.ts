import { request } from "../request";

export interface ApprovalRequest {
  id: string;
  action: string;
  target: string;
  summary: string;
  actor: string;
  status: "pending" | "approved" | "denied" | "timeout";
  created_at: number;
  resolved_at: number | null;
}

export const approvalApi = {
  /** List all currently pending approval requests. */
  listPending: () =>
    request<{ pending: ApprovalRequest[] }>("/approvals"),

  /** Get a single pending request by id. */
  getRequest: (id: string) =>
    request<ApprovalRequest>(`/approvals/${encodeURIComponent(id)}`),

  /** Approve a pending request. */
  approve: (id: string) =>
    request<{ status: string }>(`/approvals/${encodeURIComponent(id)}`, {
      method: "POST",
      body: JSON.stringify({ reply: "approved" }),
    }),

  /** Deny a pending request. */
  deny: (id: string) =>
    request<{ status: string }>(`/approvals/${encodeURIComponent(id)}`, {
      method: "POST",
      body: JSON.stringify({ reply: "denied" }),
    }),
};
