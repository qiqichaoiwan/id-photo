import request, { uploadFile } from '@/utils/request'

/**
 * 人像抠图接口
 */
export interface MattingParams {
  input_image_base64?: string;
  human_matting_model?: string;
  dpi?: number;
}

export interface MattingResult {
  status: number;
  image_base64: string;
}

/**
 * 人像抠图
 */
export function humanMatting(params: MattingParams, fileKey: string, filePath: string): Promise<MattingResult> {
  return uploadFile('/human_matting', fileKey, filePath, {
    data: params
  })
}
