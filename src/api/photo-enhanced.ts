import request, { uploadFile } from "@/utils/request";
import Method from "@/enums/Method";

/**
 * 人体抠图
 * @param data 表单数据
 * @returns 结果
 */
export const HumanMatting = (data: any, name: string, path: string): Promise<any> => {
  return uploadFile('/human_matting', name, path, { data, method: Method.POST })
}

/**
 * 证件照裁剪
 * @param data 表单数据
 * @returns 结果
 */
export const IdphotoCrop = (data: any, name: string, path: string): Promise<any> => {
  return uploadFile('/idphoto_crop', name, path, { data, method: Method.POST })
}

/**
 * 添加水印
 * @param data 表单数据
 * @returns 结果
 */
export const AddWatermark = (data: any, name: string, path: string): Promise<any> => {
  return uploadFile('/watermark', name, path, { data, method: Method.POST })
}

/**
 * 设置文件大小
 * @param data 表单数据
 * @returns 结果
 */
export const SetKb = (data: any, name: string, path: string): Promise<any> => {
  return uploadFile('/set_kb', name, path, { data, method: Method.POST })
}

/**
 * 图像增强参数接口
 */
export interface ImageEnhancementParams {
  brightness_strength?: number;  // 亮度强度，默认0
  contrast_strength?: number;    // 对比度强度，默认0
  sharpen_strength?: number;     // 锐化强度，默认0
  saturation_strength?: number;  // 饱和度强度，默认0
}

/**
 * 水印参数接口
 */
export interface WatermarkParams {
  text: string;                  // 水印文字
  size?: number;                // 字体大小，默认20
  opacity?: number;             // 透明度，默认0.5
  angle?: number;               // 旋转角度，默认30
  color?: string;               // 颜色，默认#000000
  space?: number;               // 间距，默认25
  kb?: number;                 // 文件大小
  dpi?: number;                // 分辨率，默认300
}

/**
 * 证件照裁剪参数接口
 */
export interface IdphotoCropParams {
  height: number;               // 高度
  width: number;               // 宽度
  face_detect_model?: string;   // 人脸检测模型，默认mtcnn
  hd?: boolean;                 // 是否高清，默认true
  dpi?: number;                 // 分辨率，默认300
  head_measure_ratio?: number;  // 头部比例，默认0.2
  head_height_ratio?: number;  // 头部高度比例，默认0.45
  top_distance_max?: number;   // 顶部最大距离，默认0.12
  top_distance_min?: number;   // 顶部最小距离，默认0.1
  face_align?: boolean;         // 人脸对齐，默认false
  brightness_strength?: number; // 亮度强度
  contrast_strength?: number;   // 对比度强度
  sharpen_strength?: number;    // 锐化强度
  saturation_strength?: number;  // 饱和度强度
}

/**
 * 人体抠图参数接口
 */
export interface HumanMattingParams {
  human_matting_model?: string; // 人体抠图模型，默认hivision_modnet
  dpi?: number;                 // 分辨率，默认300
}

/**
 * 设置文件大小参数接口
 */
export interface SetKbParams {
  kb: number;                   // 目标文件大小，默认50
  dpi?: number;                 // 分辨率，默认300
}
