import request from '@/utils/request';
import Method from '@/enums/Method';

export interface MembershipStatus {
  active: boolean;
  status: 'active' | 'expired' | 'none';
  expires_at: string | null;
}

export interface MembershipProfile {
  user_ref: string;
}

export interface MembershipPlan {
  id: number;
  name: string;
  months: number;
  price_fen: number;
  description: string;
  status: 'draft' | 'active' | 'archived';
}

export interface MembershipOrder {
  order_no: string;
  plan_name: string;
  months: number;
  price_fen: number;
  status: string;
  created_at: string;
  expires_at?: string | null;
  review_needed?: boolean;
  refund_request?: RefundRequest | null;
}

export interface RefundRequest {
  status: 'submitted' | 'processing' | 'closed';
  response: string;
  created_at: string;
  updated_at: string;
}

export const getMembershipStatus = (): Promise<MembershipStatus> => request('/membership/status', { method: Method.GET, timeout: 8000 });
export const getMembershipProfile = (): Promise<MembershipProfile> => request('/membership/profile', { method: Method.GET, timeout: 8000 });
export const getMembershipPlans = (): Promise<MembershipPlan[]> => request('/membership/plans', { method: Method.GET, timeout: 8000 });
export const getMembershipOrders = (): Promise<MembershipOrder[]> => request('/membership/orders', { method: Method.GET, timeout: 8000 });
export const getMembershipOrder = (orderNo: string): Promise<MembershipOrder> =>
  request(`/membership/orders/${encodeURIComponent(orderNo)}`, { method: Method.GET, timeout: 8000 });
export interface VirtualPaymentOrder {
  order_no: string;
  pay_data: { mode: string; signData: string; paySig: string; signature: string };
}
export const createMembershipOrder = (plan: MembershipPlan, code: string): Promise<VirtualPaymentOrder> =>
  request('/membership/orders', { method: Method.POST, timeout: 20000, data: { plan_id: plan.id, price_fen: plan.price_fen, months: plan.months, code } });
export const refreshMembershipOrder = (orderNo: string): Promise<MembershipOrder> =>
  request(`/membership/orders/${encodeURIComponent(orderNo)}/refresh`, { method: Method.POST, timeout: 20000 });
export const requestMembershipRefund = (orderNo: string, reason: string): Promise<RefundRequest> =>
  request(`/membership/orders/${encodeURIComponent(orderNo)}/refund-requests`, { method: Method.POST, timeout: 15000, data: { reason } });

export function formatFen(value: number): string {
  return (value / 100).toFixed(2);
}

export function formatMemberDate(value: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  // Server timestamps are UTC; membership is displayed in Beijing time.
  const china = new Date(date.getTime() + 8 * 60 * 60 * 1000);
  const pad = (n: number) => n < 10 ? `0${n}` : String(n);
  return `${china.getUTCFullYear()}-${pad(china.getUTCMonth() + 1)}-${pad(china.getUTCDate())} ${pad(china.getUTCHours())}:${pad(china.getUTCMinutes())}`;
}
