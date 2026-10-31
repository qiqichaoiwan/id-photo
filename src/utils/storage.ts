/**
 * 本地存储工具类
 * 用于管理用户历史记录和设置
 */

interface PhotoRecord {
  id: string;
  timestamp: number;
  originalImage: string;
  resultImages: {
    idPhoto: string;
    layoutPhoto?: string;
    watermarkPhoto?: string;
    mattingPhoto?: string;
  };
  parameters: {
    size: any;
    backgroundColor: string;
    isHd: boolean;
    watermark?: any;
    enhancement?: any;
    matting?: any;
  };
}

interface UserSettings {
  defaultBackgroundColor: string;
  defaultQuality: 'standard' | 'hd';
  autoSaveHistory: boolean;
  maxHistoryCount: number;
}

interface UserStatistics {
  totalPhotos: number;
  usageDays: number;
  firstUseDate: number;
  lastUseDate: number;
}

const STORAGE_KEYS = {
  USER_ID: 'photo_app_user_id',
  USER_SETTINGS: 'photo_app_settings',
  PHOTO_HISTORY: 'photo_app_history',
  STATISTICS: 'photo_app_statistics'
};

class StorageManagerClass {
  /**
   * 获取用户ID
   */
  getUserId(): string {
    let userId = uni.getStorageSync(STORAGE_KEYS.USER_ID);
    if (!userId) {
      userId = this.generateUserId();
      uni.setStorageSync(STORAGE_KEYS.USER_ID, userId);
      this.initUserData(userId);
    }
    return userId;
  }

  /**
   * 生成用户ID
   */
  private generateUserId(): string {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * 初始化用户数据
   */
  private initUserData(userId: string): void {
    const defaultSettings: UserSettings = {
      defaultBackgroundColor: '#FFFFFF',
      defaultQuality: 'hd',
      autoSaveHistory: true,
      maxHistoryCount: 50
    };

    const defaultStatistics: UserStatistics = {
      totalPhotos: 0,
      usageDays: 1,
      firstUseDate: Date.now(),
      lastUseDate: Date.now()
    };

    uni.setStorageSync(STORAGE_KEYS.USER_SETTINGS, defaultSettings);
    uni.setStorageSync(STORAGE_KEYS.STATISTICS, defaultStatistics);
    uni.setStorageSync(STORAGE_KEYS.PHOTO_HISTORY, []);
  }

  /**
   * 保存照片记录
   */
  savePhotoRecord(record: Omit<PhotoRecord, 'id' | 'timestamp'>): string {
    const id = 'photo_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const fullRecord: PhotoRecord = {
      ...record,
      id,
      timestamp: Date.now()
    };

    const history = this.getPhotoHistory();
    history.unshift(fullRecord);

    // 限制历史记录数量
    const settings = this.getUserSettings();
    if (history.length > settings.maxHistoryCount) {
      history.splice(settings.maxHistoryCount);
    }

    uni.setStorageSync(STORAGE_KEYS.PHOTO_HISTORY, history);
    this.updateStatistics('add');
    return id;
  }

  /**
   * 获取照片历史记录
   */
  getPhotoHistory(): PhotoRecord[] {
    return uni.getStorageSync(STORAGE_KEYS.PHOTO_HISTORY) || [];
  }

  /**
   * 删除照片记录
   */
  deletePhotoRecord(id: string): boolean {
    const history = this.getPhotoHistory();
    const index = history.findIndex(record => record.id === id);
    if (index !== -1) {
      history.splice(index, 1);
      uni.setStorageSync(STORAGE_KEYS.PHOTO_HISTORY, history);
      this.updateStatistics('delete');
      return true;
    }
    return false;
  }

  /**
   * 清空照片历史记录
   */
  clearPhotoHistory(): void {
    uni.setStorageSync(STORAGE_KEYS.PHOTO_HISTORY, []);
    const statistics = this.getUserStatistics();
    statistics.totalPhotos = 0;
    uni.setStorageSync(STORAGE_KEYS.STATISTICS, statistics);
  }

  /**
   * 获取用户设置
   */
  getUserSettings(): UserSettings {
    return uni.getStorageSync(STORAGE_KEYS.USER_SETTINGS) || {
      defaultBackgroundColor: '#FFFFFF',
      defaultQuality: 'hd',
      autoSaveHistory: true,
      maxHistoryCount: 50
    };
  }

  /**
   * 更新用户设置
   */
  updateUserSettings(settings: Partial<UserSettings>): void {
    const currentSettings = this.getUserSettings();
    const newSettings = { ...currentSettings, ...settings };
    uni.setStorageSync(STORAGE_KEYS.USER_SETTINGS, newSettings);
  }

  /**
   * 获取用户统计信息
   */
  getUserStatistics(): UserStatistics {
    const statistics = uni.getStorageSync(STORAGE_KEYS.STATISTICS);
    if (statistics) {
      // 更新使用天数
      const today = new Date().toDateString();
      const lastUse = new Date(statistics.lastUseDate).toDateString();
      if (today !== lastUse) {
        statistics.usageDays += 1;
        statistics.lastUseDate = Date.now();
        uni.setStorageSync(STORAGE_KEYS.STATISTICS, statistics);
      }
      return statistics;
    }
    return {
      totalPhotos: 0,
      usageDays: 1,
      firstUseDate: Date.now(),
      lastUseDate: Date.now()
    };
  }

  /**
   * 更新统计信息
   */
  recordPhotoCreated(): void { this.updateStatistics('add'); }

  private updateStatistics(action: 'add' | 'delete'): void {
    const statistics = this.getUserStatistics();
    statistics.lastUseDate = Date.now();
    
    if (action === 'add') {
      statistics.totalPhotos += 1;
    } else if (action === 'delete' && statistics.totalPhotos > 0) {
      statistics.totalPhotos -= 1;
    }
    
    uni.setStorageSync(STORAGE_KEYS.STATISTICS, statistics);
  }

  /**
   * 清理缓存
   */
  static clearCache() {
    try {
      const keys = [
        STORAGE_KEYS.USER_ID,
        STORAGE_KEYS.USER_SETTINGS,
        STORAGE_KEYS.PHOTO_HISTORY,
        STORAGE_KEYS.STATISTICS
      ];
      
      keys.forEach(key => {
        uni.removeStorageSync(key);
      });
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }
}

const StorageManager = new StorageManagerClass();

export default StorageManager;
export { PhotoRecord, UserSettings, UserStatistics };
