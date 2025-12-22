// 电子照功能测试脚本
// 在小程序开发者工具控制台中运行此脚本来测试电子照功能

console.log('=== 开始测试电子照功能 ===');

// 测试1: 检查电子照管理器是否可用
try {
  const ElectronicPhotoManager = require('@/utils/electronic-photo').ElectronicPhotoManager;
  console.log('✅ 电子照管理器加载成功');
} catch (error) {
  console.error('❌ 电子照管理器加载失败:', error);
}

// 测试2: 检查当前电子照数量
try {
  const photos = uni.getStorageSync('electronic_photos') || [];
  console.log('📊 当前电子照数量:', photos.length);
  console.log('📝 电子照数据:', photos);
} catch (error) {
  console.error('❌ 读取电子照数据失败:', error);
}

// 测试3: 手动添加测试数据
try {
  const testPhoto = {
    id: 'test_' + Date.now(),
    name: '测试证件照',
    size: '295×413',
    color: '#FFFFFF',
    hdBase64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', // 1x1透明像素
    sdBase64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    createdAt: Date.now(),
    expireAt: Date.now() + (30 * 24 * 60 * 60 * 1000) // 30天后过期
  };
  
  const existingPhotos = uni.getStorageSync('electronic_photos') || [];
  existingPhotos.push(testPhoto);
  uni.setStorageSync('electronic_photos', existingPhotos);
  
  console.log('✅ 测试数据添加成功');
  console.log('📝 测试数据:', testPhoto);
} catch (error) {
  console.error('❌ 添加测试数据失败:', error);
}

// 测试4: 重新检查电子照数量
try {
  const photos = uni.getStorageSync('electronic_photos') || [];
  console.log('📊 添加后电子照数量:', photos.length);
  console.log('📝 所有电子照数据:', photos);
} catch (error) {
  console.error('❌ 重新读取失败:', error);
}

console.log('=== 测试完成 ===');
console.log('💡 提示: 请检查电子照页面是否显示测试数据');
