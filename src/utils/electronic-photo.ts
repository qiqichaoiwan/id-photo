/**
 * 电子照存储管理工具
 * 使用小程序本地缓存实现限时缓存数量
 */

export interface ElectronicPhoto {
  id: string;
  name: string;
  size: string;
  color: string;
  hdBase64: string;
  sdBase64: string;
  createdAt: number;
}

export class ElectronicPhotoManager {
  private static readonly STORAGE_KEY = 'electronic_photos';
  private static readonly MAX_COUNT = 2; // 最多保存2张

  /**
   * 检查是否可以保存更多电子照
   */
  static canSaveMore(): boolean {
    try {
      const photos = this.getAll();
      return photos.length < this.MAX_COUNT;
    } catch (error) {
      console.error('检查电子照数量失败:', error);
      return false;
    }
  }

  /**
   * 压缩base64图片数据
   */
  static compressBase64(base64Data: string, maxWidth: number = 800, quality: number = 0.8): Promise<string> {
    return new Promise((resolve) => {
      try {
        // 如果不是base64格式，直接返回
        if (!base64Data.startsWith('data:')) {
          resolve(base64Data);
          return;
        }

        // 创建临时canvas进行压缩
        uni.createSelectorQuery()
          .select('#compress-canvas')
          .fields({ node: true, size: true }, () => {})
          .exec((res) => {
            if (!res[0] || !res[0].node) {
              // 如果没有canvas节点，使用简单压缩策略
              const compressedBase64 = this.simpleCompress(base64Data);
              resolve(compressedBase64);
              return;
            }

            const canvas = res[0].node;
            const ctx = canvas.getContext('2d');
            
            // 创建图片对象
            const img = canvas.createImage();
            img.onload = () => {
              // 计算压缩后的尺寸
              let { width, height } = img;
              if (width > maxWidth) {
                height = (height * maxWidth) / width;
                width = maxWidth;
              }

              // 设置canvas尺寸
              canvas.width = width;
              canvas.height = height;

              // 绘制压缩后的图片
              ctx.drawImage(img, 0, 0, width, height);

              // 转换为base64
              const compressedBase64 = canvas.toDataURL('image/jpeg', quality);
              resolve(compressedBase64);
            };
            img.onerror = () => {
              // 压缩失败，使用简单压缩
              const compressedBase64 = this.simpleCompress(base64Data);
              resolve(compressedBase64);
            };
            img.src = base64Data;
          });
      } catch (error) {
        console.error('压缩图片失败:', error);
        // 压缩失败，使用简单压缩
        const compressedBase64 = this.simpleCompress(base64Data);
        resolve(compressedBase64);
      }
    });
  }

  /**
   * 简单压缩策略 - 小程序存储优化版本
   */
  static simpleCompress(base64Data: string): string {
    try {
      console.log('开始压缩，原始大小:', (base64Data.length / 1024).toFixed(2) + 'KB');
      
      // 设置目标大小：小程序存储限制约为10MB，单张图片控制在2MB以内
      const targetMaxSize = 2 * 1024 * 1024; // 2MB
      const targetMinSize = 500 * 1024; // 500KB
      
      // 如果数据已经很小，直接返回
      if (base64Data.length < targetMinSize) {
        console.log('图片数据较小，跳过压缩:', (base64Data.length / 1024).toFixed(2) + 'KB');
        return base64Data;
      }

      // 如果数据太大，进行质量压缩
      if (base64Data.length > targetMaxSize) {
        console.log('图片过大，进行质量压缩:', (base64Data.length / 1024).toFixed(2) + 'KB');
        return this.qualityCompress(base64Data, targetMaxSize);
      }

      // 对于中等大小的图片，进行尺寸压缩
      if (base64Data.length > targetMinSize) {
        console.log('图片中等大小，进行尺寸压缩:', (base64Data.length / 1024).toFixed(2) + 'KB');
        return this.sizeCompress(base64Data);
      }

      return base64Data;
    } catch (error) {
      console.error('压缩失败:', error);
      return base64Data;
    }
  }

  /**
   * 质量压缩 - 减少JPEG质量
   */
  static qualityCompress(base64Data: string, targetSize: number): string {
    try {
      // 对于PNG，尝试转换为JPEG以节省空间
      if (base64Data.startsWith('data:image/png;base64,')) {
        const base64Content = base64Data.replace('data:image/png;base64,', '');
        
        // 检查是否包含透明度信息
        if (this.hasTransparency(base64Content)) {
          console.log('检测到透明PNG，保持PNG格式但进行采样压缩');
          return this.sampleCompress(base64Data, targetSize);
        } else {
          console.log('转换为JPEG格式以节省空间');
          const jpegBase64 = 'data:image/jpeg;base64,' + base64Content;
          return this.sampleCompress(jpegBase64, targetSize);
        }
      }

      return this.sampleCompress(base64Data, targetSize);
    } catch (error) {
      console.error('质量压缩失败:', error);
      return base64Data;
    }
  }

  /**
   * 尺寸压缩 - 通过采样减少分辨率
   */
  static sizeCompress(base64Data: string): string {
    try {
      const targetSize = 800 * 1024; // 800KB
      return this.sampleCompress(base64Data, targetSize);
    } catch (error) {
      console.error('尺寸压缩失败:', error);
      return base64Data;
    }
  }

  /**
   * 采样压缩 - 通过减少数据量来压缩
   */
  static sampleCompress(base64Data: string, targetSize: number): string {
    try {
      // 获取纯base64数据
      const parts = base64Data.split(',');
      const prefix = parts[0] + ',';
      const base64Content = parts[1] || parts[0];
      
      // 计算压缩比例
      const currentSize = base64Content.length;
      const compressionRatio = Math.max(0.3, targetSize / currentSize); // 最低保留30%
      
      // 采样压缩：每隔几个字符取一个
      const sampleRate = Math.ceil(1 / compressionRatio);
      let compressedContent = '';
      
      for (let i = 0; i < base64Content.length; i += sampleRate) {
        compressedContent += base64Content[i];
      }

      // 确保base64格式正确（填充到4的倍数）
      while (compressedContent.length % 4 !== 0) {
        compressedContent += '=';
      }

      const compressedBase64 = prefix + compressedContent;
      
      console.log('采样压缩完成:', {
        原始大小: (currentSize / 1024).toFixed(2) + 'KB',
        压缩后: (compressedBase64.length / 1024).toFixed(2) + 'KB',
        压缩比: ((currentSize - compressedBase64.length) / currentSize * 100).toFixed(1) + '%'
      });

      return compressedBase64;
    } catch (error) {
      console.error('采样压缩失败:', error);
      return base64Data;
    }
  }

  /**
   * 检查PNG是否包含透明度信息
   */
  static hasTransparency(base64Content: string): boolean {
    try {
      // 简单检查PNG的透明度标记
      return base64Content.includes('tRNS') || 
             base64Content.includes('PLTE') && base64Content.includes('alpha') ||
             base64Content.length > 500000; // 大图片可能有透明度
    } catch (error) {
      console.error('透明度检查失败:', error);
      return true; // 安全起见，假设有透明度
    }
  }

  /**
   * 保存电子照
   */
  static save(photo: Omit<ElectronicPhoto, 'id' | 'createdAt'>): boolean {
    try {
      console.log('开始保存电子照:', photo);
      
      // 确保base64数据格式正确
      const processedPhoto = {
        ...photo,
        hdBase64: photo.hdBase64.startsWith('data:') ? photo.hdBase64 : `data:image/png;base64,${photo.hdBase64}`,
        sdBase64: photo.sdBase64.startsWith('data:') ? photo.sdBase64 : `data:image/png;base64,${photo.sdBase64}`
      };
      
      console.log('处理后的电子照数据:', processedPhoto);
      
      const photos = this.getAll();
      
      // 检查是否超过最大数量
      if (photos.length >= this.MAX_COUNT) {
        // 删除最旧的照片
        photos.sort((a: ElectronicPhoto, b: ElectronicPhoto) => a.createdAt - b.createdAt);
        photos.splice(0, photos.length - this.MAX_COUNT + 1);
      }

      const now = Date.now();
      const newPhoto: ElectronicPhoto = {
        ...processedPhoto,
        id: this.generateId(),
        createdAt: now
      };

      photos.push(newPhoto);
      console.log('保存后的电子照列表:', photos);
      
      // 强制同步存储
      uni.setStorageSync(this.STORAGE_KEY, photos);
      
      // 验证存储是否成功
      const storedPhotos = uni.getStorageSync(this.STORAGE_KEY);
      console.log('验证存储的数据:', storedPhotos);
      console.log('存储的数据长度:', storedPhotos ? storedPhotos.length : 0);
      
      return true;
    } catch (error) {
      console.error('保存电子照失败:', error);
      return false;
    }
  }

  /**
   * 获取所有电子照
   */
  static getAll(): ElectronicPhoto[] {
    try {
      const photos = uni.getStorageSync(this.STORAGE_KEY) || [];
      
      // 直接返回所有照片，不再过滤过期照片
      return photos.sort((a: ElectronicPhoto, b: ElectronicPhoto) => b.createdAt - a.createdAt);
    } catch (error) {
      console.error('获取电子照列表失败:', error);
      return [];
    }
  }

  /**
   * 获取单个电子照
   */
  static getById(id: string): ElectronicPhoto | null {
    try {
      const photos = this.getAll();
      return photos.find(photo => photo.id === id) || null;
    } catch (error) {
      console.error('获取电子照失败:', error);
      return null;
    }
  }

  /**
   * 删除电子照
   */
  static delete(id: string): boolean {
    try {
      const photos = this.getAll();
      const filteredPhotos = photos.filter(photo => photo.id !== id);
      uni.setStorageSync(this.STORAGE_KEY, filteredPhotos);
      return true;
    } catch (error) {
      console.error('删除电子照失败:', error);
      return false;
    }
  }

  /**
   * 清空所有电子照
   */
  static clear(): boolean {
    try {
      uni.removeStorageSync(this.STORAGE_KEY);
      return true;
    } catch (error) {
      console.error('清空电子照失败:', error);
      return false;
    }
  }

  /**
   * 获取存储统计信息
   */
  static getStats(): { total: number; size: string; oldestDate: string | null } {
    try {
      const photos = this.getAll();
      const total = photos.length;
      
      // 计算存储大小（粗略估算）
      const sizeInBytes = photos.reduce((total, photo) => {
        return total + photo.hdBase64.length + photo.sdBase64.length;
      }, 0);
      const sizeInMB = (sizeInBytes / (1024 * 1024)).toFixed(2);
      
      // 获取最早的照片日期，格式化为 YYYY-MM-dd
      const oldestDate = photos.length > 0 
        ? this.formatDateString(Math.min(...photos.map(p => p.createdAt)))
        : null;
      
      return {
        total,
        size: `${sizeInMB}MB`,
        oldestDate
      };
    } catch (error) {
      console.error('获取统计信息失败:', error);
      return { total: 0, size: '0MB', oldestDate: null };
    }
  }

  /**
   * 格式化日期为 YYYY-MM-dd
   */
  static formatDateString(timestamp: number): string {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * 生成唯一ID
   */
  private static generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

}
