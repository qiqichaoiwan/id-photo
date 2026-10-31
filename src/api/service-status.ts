import { baseUrl } from '@/config';

export type CheckState = 'ok' | 'degraded' | 'unavailable' | 'disabled' | 'unknown';
export interface ServiceCheck { id: string; name: string; state: CheckState; detail: string; }
export interface ServiceSnapshot {
  status: 'ok' | 'degraded';
  checked_at: string;
  checks: ServiceCheck[];
  note: string;
}

const allowedStates: CheckState[] = ['ok', 'degraded', 'unavailable', 'disabled', 'unknown'];

export function fetchServiceStatus(): Promise<ServiceSnapshot> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${baseUrl}/service-status`, method: 'GET', timeout: 8000,
      success: (response: any) => {
        const data = response.data;
        if (response.statusCode !== 200 || !data ||
            (data.status !== 'ok' && data.status !== 'degraded') ||
            typeof data.checked_at !== 'string' || typeof data.note !== 'string' || !Array.isArray(data.checks) ||
            !data.checks.every((item: any) => item && typeof item.id === 'string' &&
              typeof item.name === 'string' && typeof item.detail === 'string' && allowedStates.indexOf(item.state) >= 0)) {
          reject(new Error('服务状态暂不可用')); return;
        }
        resolve(data as ServiceSnapshot);
      },
      fail: () => reject(new Error('暂时无法连接服务'))
    });
  });
}
