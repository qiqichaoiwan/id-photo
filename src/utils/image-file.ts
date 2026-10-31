declare const wx: any;

const ownedPattern = /^(?:(?:idphoto[-_]|temp_color_|layout_|matting_|watermark_|electronic_photo_|photo_)[a-z0-9_-]+\.(?:png|jpe?g|webp)|temp_image(?:_hd)?\.png)$/i;

export function writeTemporaryImage(data: string, purpose: string): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!data || typeof data !== 'string') { reject(new Error('服务器未返回图片')); return; }
    const match = data.match(/^data:image\/(png|jpeg|jpg|webp);base64,/i);
    const extension = match ? (match[1].toLowerCase() === 'jpeg' ? 'jpg' : match[1].toLowerCase()) : 'png';
    const contents = match ? data.slice(match[0].length) : data;
    // #ifdef MP-WEIXIN
    const name = purpose.replace(/[^a-z0-9-]/gi, '').slice(0, 30) || 'image';
    const path = `${wx.env.USER_DATA_PATH}/idphoto-${name}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}.${extension}`;
    uni.getFileSystemManager().writeFile({
      filePath: path, data: contents, encoding: 'base64',
      success: () => resolve(path),
      fail: () => reject(new Error('保存临时图片失败，请检查设备存储空间'))
    });
    // #endif
    // #ifndef MP-WEIXIN
    reject(new Error('当前环境不支持本地图片处理'));
    // #endif
  });
}

export function removeTemporaryImage(path: string): void {
  // #ifdef MP-WEIXIN
  const prefix = `${wx.env.USER_DATA_PATH}/`;
  if (!path || !path.startsWith(prefix) || !ownedPattern.test(path.slice(prefix.length))) return;
  uni.getFileSystemManager().unlink({ filePath: path, fail: () => {} });
  // #endif
}

export function clearTemporaryImages(): Promise<void> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    const fs = uni.getFileSystemManager();
    fs.readdir({
      dirPath: wx.env.USER_DATA_PATH,
      success: ({ files }: any) => {
        const owned = files.filter((name: string) => ownedPattern.test(name));
        Promise.all(owned.map((name: string) => new Promise<void>((ok, fail) => {
          fs.unlink({ filePath: `${wx.env.USER_DATA_PATH}/${name}`, success: () => ok(), fail: () => fail(new Error('部分临时图片清理失败')) });
        }))).then(() => resolve()).catch(reject);
      },
      fail: () => reject(new Error('读取临时图片失败'))
    });
    // #endif
    // #ifndef MP-WEIXIN
    resolve();
    // #endif
  });
}
