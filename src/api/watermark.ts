import request, { uploadFile } from '@/utils/request'

/**
 * 图片加水印接口
 */
export interface WatermarkParams {
  input_image_base64?: string;
  text?: string;
  size?: number;
  opacity?: number;
  angle?: number;
  color?: string;
  space?: number;
  dpi?: number;
}

export interface WatermarkResult {
  status: number;
  image_base64: string;
}

/**
 * 图片加水印
 */
export function addWatermark(params: WatermarkParams, fileKey: string, filePath: string): Promise<WatermarkResult> {
  return uploadFile('/watermark', fileKey, filePath, {
    data: params
  })
}

/**
 * 设置图像KB大小
 */
export interface SetKbParams {
  input_image_base64?: string;
  kb?: number;
  dpi?: number;
}

export interface SetKbResult {
  status: number;
  image_base64: string;
}

/**
 * 设置图像KB大小
 */
export function setKb(params: SetKbParams, fileKey: string, filePath: string): Promise<SetKbResult> {
  return uploadFile('/set_kb', fileKey, filePath, {
    data: params
  })
}
