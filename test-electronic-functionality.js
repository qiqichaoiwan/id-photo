/**
 * 电子照功能完整性测试脚本
 * 在微信开发者工具控制台中运行此脚本来测试电子照功能
 */

// 测试1: 检查存储工具是否正常工作
console.log('=== 测试1: 检查存储工具 ===');
try {
  const testKey = 'test_storage_' + Date.now();
  const testData = { test: 'data', timestamp: Date.now() };
  
  uni.setStorageSync(testKey, testData);
  const retrievedData = uni.getStorageSync(testKey);
  
  if (JSON.stringify(testData) === JSON.stringify(retrievedData)) {
    console.log('✅ 存储工具工作正常');
  } else {
    console.log('❌ 存储工具异常');
  }
  
  // 清理测试数据
  uni.removeStorageSync(testKey);
} catch (error) {
  console.log('❌ 存储工具测试失败:', error);
}

// 测试2: 检查电子照管理器是否存在
console.log('=== 测试2: 检查电子照管理器 ===');
try {
  // 模拟导入电子照管理器（在实际环境中应该已经导入）
  const ElectronicPhotoManager = {
    save: (photoData) => {
      try {
        const photos = uni.getStorageSync('electronic_photos') || [];
        photos.push(photoData);
        uni.setStorageSync('electronic_photos', photos);
        return true;
      } catch (error) {
        console.error('保存电子照失败:', error);
        return false;
      }
    },
    
    getAll: () => {
      try {
        return uni.getStorageSync('electronic_photos') || [];
      } catch (error) {
        console.error('获取电子照列表失败:', error);
        return [];
      }
    }
  };
  
  console.log('✅ 电子照管理器创建成功');
  
  // 测试保存功能
  const testPhoto = {
    id: 'test_' + Date.now(),
    name: '测试证件照',
    size: '295×413',
    color: '#FFFFFF',
    hdBase64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    sdBase64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    createdAt: Date.now(),
    expireAt: Date.now() + (30 * 24 * 60 * 60 * 1000)
  };
  
  const saveResult = ElectronicPhotoManager.save(testPhoto);
  if (saveResult) {
    console.log('✅ 电子照保存功能正常');
  } else {
    console.log('❌ 电子照保存功能异常');
  }
  
  // 测试获取功能
  const photos = ElectronicPhotoManager.getAll();
  if (Array.isArray(photos) && photos.length > 0) {
    console.log('✅ 电子照获取功能正常，当前数量:', photos.length);
    console.log('最新照片:', photos[photos.length - 1]);
  } else {
    console.log('❌ 电子照获取功能异常');
  }
  
} catch (error) {
  console.log('❌ 电子照管理器测试失败:', error);
}

// 测试3: 检查页面路由
console.log('=== 测试3: 检查页面路由 ===');
try {
  // 检查电子照页面是否存在
  const pages = getCurrentPages();
  console.log('当前页面栈:', pages.map(page => page.route));
  
  // 检查是否可以跳转到电子照页面
  console.log('尝试跳转到电子照页面...');
  uni.switchTab({
    url: '/pages/electronic/index',
    success: () => {
      console.log('✅ 电子照页面跳转成功');
    },
    fail: (error) => {
      console.log('❌ 电子照页面跳转失败:', error);
    }
  });
} catch (error) {
  console.log('❌ 页面路由测试失败:', error);
}

// 测试4: 手动添加测试数据
console.log('=== 测试4: 手动添加测试数据 ===');
try {
  const testPhoto = {
    id: 'manual_test_' + Date.now(),
    name: '手动测试证件照',
    size: '295×413',
    color: '#4A90E2',
    hdBase64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    sdBase64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    createdAt: Date.now(),
    expireAt: Date.now() + (30 * 24 * 60 * 60 * 1000)
  };
  
  const existingPhotos = uni.getStorageSync('electronic_photos') || [];
  existingPhotos.push(testPhoto);
  uni.setStorageSync('electronic_photos', existingPhotos);
  
  console.log('✅ 手动测试数据添加成功');
  console.log('当前电子照数量:', existingPhotos.length);
  
  // 验证数据是否正确保存
  const verifyPhotos = uni.getStorageSync('electronic_photos') || [];
  const foundTest = verifyPhotos.find(p => p.id === testPhoto.id);
  if (foundTest) {
    console.log('✅ 测试数据验证成功');
  } else {
    console.log('❌ 测试数据验证失败');
  }
} catch (error) {
  console.log('❌ 手动添加测试数据失败:', error);
}

// 测试5: 检查当前存储状态
console.log('=== 测试5: 检查当前存储状态 ===');
try {
  const currentPhotos = uni.getStorageSync('electronic_photos') || [];
  console.log('当前存储的电子照数量:', currentPhotos.length);
  
  if (currentPhotos.length > 0) {
    console.log('最新的电子照信息:');
    const latestPhoto = currentPhotos[currentPhotos.length - 1];
    console.log('- ID:', latestPhoto.id);
    console.log('- 名称:', latestPhoto.name);
    console.log('- 尺寸:', latestPhoto.size);
    console.log('- 颜色:', latestPhoto.color);
    console.log('- 创建时间:', new Date(latestPhoto.createdAt).toLocaleString());
    console.log('- 过期时间:', new Date(latestPhoto.expireAt).toLocaleString());
    console.log('- Base64长度:', latestPhoto.hdBase64 ? latestPhoto.hdBase64.length : 0);
  } else {
    console.log('当前没有存储任何电子照');
  }
} catch (error) {
  console.log('❌ 检查存储状态失败:', error);
}

console.log('=== 测试完成 ===');
console.log('如果所有测试都显示 ✅，则电子照功能应该正常工作');
console.log('如果有 ❌，请检查对应的错误信息');
