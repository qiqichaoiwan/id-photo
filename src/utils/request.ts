import { baseUrl } from '@/config';
import Method from '@/enums/Method';
import { Result, RequestOptions } from '@/model/Result';
import { currentToken, invalidateToken, loginToBackend } from '@/utils/auth';

const timeout = 120000;

function responseError(status: number, body: any): Error {
  if (status === 429) return new Error('操作过于频繁，请稍后再试');
  if (status >= 500) return new Error('服务暂不可用，请稍后再试');
  return new Error(typeof body?.detail === 'string' ? body.detail :
    (typeof body?.message === 'string' ? body.message : '请求失败，请稍后重试'));
}

function checkResponse<T>(status: number, data: any): T {
  let body = data;
  if (typeof data === 'string') {
    try { body = JSON.parse(data); } catch (_) {
      throw new Error('服务器返回的数据无法读取，请稍后重试');
    }
  }
  if (status < 200 || status >= 300) throw responseError(status, body);
  if (body && body.status === false) {
    throw new Error(body.message || body.error || '图片处理失败，请检查照片后重试');
  }
  return body as T;
}

function authHeaders(): AnyObject {
  const token = currentToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function withLoginRetry<T>(action: () => Promise<T>, useBackend: boolean): Promise<T> {
  // Avoid sending an image twice on the first request to a protected backend.
  if (useBackend && process.env.VUE_APP_BACKEND_AUTH_REQUIRED !== 'false' && !currentToken()) {
    await loginToBackend();
  }
  try {
    return await action();
  } catch (error: any) {
    if (!useBackend || error?.statusCode !== 401) throw error;
    invalidateToken();
    await loginToBackend();
    return action();
  }
}

function unauthorized(): Error {
  const error: any = new Error('登录状态已过期');
  error.statusCode = 401;
  return error;
}

const request = async <T>(url: string, options: RequestOptions = { method: Method.GET }): Promise<T> => {
  const { method, data, gateway, loading, headers, remoteUrl, timeout: requestTimeout } = options;
  const targetUrl = remoteUrl || baseUrl;
  const useBackend = targetUrl === baseUrl;
  if (loading) uni.showLoading();
  try {
    return await withLoginRetry(() => new Promise<T>((resolve, reject) => {
      uni.request({
        url: targetUrl + (gateway || '') + url,
        method: method || Method.GET,
        data,
        timeout: requestTimeout || timeout,
        header: { 'Content-Type': 'application/json; charset=UTF-8', ...(headers || {}), ...(useBackend ? authHeaders() : {}) },
        success: ({ data: response, statusCode }: any) => {
          if (statusCode === 401 && useBackend) { reject(unauthorized()); return; }
          try {
            const body: any = checkResponse(statusCode, response);
            if (body && typeof body.code === 'number') {
              if (body.code !== 200) throw new Error(body.message || '请求失败，请重试');
              resolve((body as Result<T>).data);
            } else resolve(body);
          } catch (error) { reject(error); }
        },
        fail: () => reject(new Error('网络连接失败，请检查网络后重试'))
      });
    }), useBackend);
  } finally {
    if (loading) uni.hideLoading();
  }
};

export const uploadFile = async <T>(
  url: string,
  name: string,
  path: string,
  options: RequestOptions = { method: Method.POST }
): Promise<T> => {
  if (!path) throw new Error('图片路径无效，请重新选择照片');
  const formData: AnyObject = {};
  Object.keys(options.data || {}).forEach((key) => {
    const value = options.data[key];
    if (value !== undefined && value !== null) formData[key] = String(value);
  });
  return withLoginRetry(() => new Promise<T>((resolve, reject) => {
    uni.uploadFile({
      url: baseUrl + (options.gateway || '') + url,
      filePath: path,
      name,
      formData,
      timeout,
      header: authHeaders(),
      success: ({ data, statusCode }: any) => {
        if (Number(statusCode) === 401) { reject(unauthorized()); return; }
        try { resolve(checkResponse<T>(Number(statusCode), data)); }
        catch (error) { reject(error); }
      },
      fail: () => reject(new Error('图片上传失败，请检查网络后重试'))
    });
  }), true);
};

export default request;
