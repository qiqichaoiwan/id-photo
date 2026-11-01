import { uploadFile } from '@/utils/request';

export interface ContentSecurityResult {
  safe: boolean | null;
  available: boolean;
  errcode: number;
  errmsg: string;
  trace_id: string;
  sha256: string;
  checked_at: string;
  accepted?: boolean;
}

export function checkImageSecurity(path: string): Promise<ContentSecurityResult> {
  return uploadFile<ContentSecurityResult>('/content-security/image', 'input_image', path);
}
