import Method from '@/enums/Method';
import request, { uploadFile } from '@/utils/request';

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

export interface TextSecurityRequest {
  content: string;
  scene?: number;
  title?: string;
}

export interface MediaSecurityRequest {
  media_url: string;
  media_type?: number;
  scene?: number;
}

export function checkImageSecurity(path: string): Promise<ContentSecurityResult> {
  return uploadFile<ContentSecurityResult>('/content-security/image', 'input_image', path);
}

/**
 * Run the same msg_sec_check flow used by user supplied text fields.
 * The request helper adds the mini-program login token and retries once after
 * an expired token, just like image processing requests.
 */
export function checkTextSecurity(data: TextSecurityRequest): Promise<ContentSecurityResult> {
  return request<ContentSecurityResult>('/content-security/text', {
    method: Method.POST,
    data,
  });
}

/**
 * Submit a publicly reachable HTTPS media URL to media_check_async. The
 * result is an acceptance receipt; the final verdict is delivered by the
 * WeChat message-push callback and is recorded by the backend.
 */
export function checkMediaSecurity(data: MediaSecurityRequest): Promise<ContentSecurityResult> {
  return request<ContentSecurityResult>('/content-security/media', {
    method: Method.POST,
    data,
  });
}
