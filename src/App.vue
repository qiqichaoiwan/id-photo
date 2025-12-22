<script lang="ts">
import Vue from 'vue';
import StorageManager from '@/utils/storage';

// 声明微信小程序类型
declare const wx: any;

export default Vue.extend({
    mpType: 'app',
    onLaunch() {
        console.log('App Launch');
        this.initApp();
        this.initGlobalShare();
    },
    onShow() {
        console.log('App Show');
        // #ifndef APP-NVUE
        uni.requireNativePlugin = () => { };
        // #endif
    },
    onHide() {
        console.log('App Hide');
    },
    methods: {
        /**
         * 初始化应用
         */
        initApp() {
            try {
                // 初始化存储系统
                StorageManager.getUserId();
                console.log('Storage initialized successfully');
                
                // 检查更新（可选）
                this.checkForUpdate();
                
            } catch (error) {
                console.error('App initialization failed:', error);
            }
        },
        
        /**
         * 初始化全局分享功能
         */
        initGlobalShare() {
            // #ifdef MP-WEIXIN
            // 全局开启分享功能
            wx.showShareMenu({
                withShareTicket: true,
                menus: ['shareAppMessage', 'shareTimeline'],
                success: () => {
                    console.log('全局分享功能开启成功');
                },
                fail: (err: any) => {
                    console.error('全局分享功能开启失败:', err);
                }
            });
            // #endif
        },
        
        /**
         * 检查应用更新
         */
        checkForUpdate() {
            // #ifdef MP-WEIXIN
            const updateManager = uni.getUpdateManager();
            
            updateManager.onCheckForUpdate((res) => {
                console.log('Update check result:', res.hasUpdate);
            });
            
            updateManager.onUpdateReady(() => {
                uni.showModal({
                    title: '更新提示',
                    content: '新版本已经准备好，是否重启应用？',
                    success(res) {
                        if (res.confirm) {
                            updateManager.applyUpdate();
                        }
                    }
                });
            });
            
            updateManager.onUpdateFailed(() => {
                uni.showToast({
                    title: '更新失败',
                    icon: 'none'
                });
            });
            // #endif
        }
    }
});
</script>

<style lang="scss">
@import "uview-ui/index.scss";

/* 全局样式 */
page {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    background-color: #f8f9fa;
}

/* 自定义滚动条样式 */
::-webkit-scrollbar {
    width: 6rpx;
    height: 6rpx;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3rpx;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3rpx;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* 通用动画类 */
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s;
}

.fade-enter, .fade-leave-to {
    opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
    transition: transform 0.3s;
}

.slide-up-enter, .slide-up-leave-to {
    transform: translateY(100%);
}

.scale-enter-active, .scale-leave-active {
    transition: transform 0.3s;
}

.scale-enter, .scale-leave-to {
    transform: scale(0.8);
}

/* 通用工具类 */
.text-center {
    text-align: center;
}

.text-left {
    text-align: left;
}

.text-right {
    text-align: right;
}

.flex {
    display: flex;
}

.flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
}

.flex-between {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.flex-column {
    display: flex;
    flex-direction: column;
}

.flex-wrap {
    flex-wrap: wrap;
}

.flex-1 {
    flex: 1;
}

.w-full {
    width: 100%;
}

.h-full {
    height: 100%;
}

.relative {
    position: relative;
}

.absolute {
    position: absolute;
}

.fixed {
    position: fixed;
}

.z-10 {
    z-index: 10;
}

.z-20 {
    z-index: 20;
}

.z-30 {
    z-index: 30;
}

/* 间距工具类 */
.m-0 { margin: 0; }
.m-1 { margin: 8rpx; }
.m-2 { margin: 16rpx; }
.m-3 { margin: 24rpx; }
.m-4 { margin: 32rpx; }

.mt-0 { margin-top: 0; }
.mt-1 { margin-top: 8rpx; }
.mt-2 { margin-top: 16rpx; }
.mt-3 { margin-top: 24rpx; }
.mt-4 { margin-top: 32rpx; }

.mb-0 { margin-bottom: 0; }
.mb-1 { margin-bottom: 8rpx; }
.mb-2 { margin-bottom: 16rpx; }
.mb-3 { margin-bottom: 24rpx; }
.mb-4 { margin-bottom: 32rpx; }

.ml-0 { margin-left: 0; }
.ml-1 { margin-left: 8rpx; }
.ml-2 { margin-left: 16rpx; }
.ml-3 { margin-left: 24rpx; }
.ml-4 { margin-left: 32rpx; }

.mr-0 { margin-right: 0; }
.mr-1 { margin-right: 8rpx; }
.mr-2 { margin-right: 16rpx; }
.mr-3 { margin-right: 24rpx; }
.mr-4 { margin-right: 32rpx; }

.p-0 { padding: 0; }
.p-1 { padding: 8rpx; }
.p-2 { padding: 16rpx; }
.p-3 { padding: 24rpx; }
.p-4 { padding: 32rpx; }

.pt-0 { padding-top: 0; }
.pt-1 { padding-top: 8rpx; }
.pt-2 { padding-top: 16rpx; }
.pt-3 { padding-top: 24rpx; }
.pt-4 { padding-top: 32rpx; }

.pb-0 { padding-bottom: 0; }
.pb-1 { padding-bottom: 8rpx; }
.pb-2 { padding-bottom: 16rpx; }
.pb-3 { padding-bottom: 24rpx; }
.pb-4 { padding-bottom: 32rpx; }

.pl-0 { padding-left: 0; }
.pl-1 { padding-left: 8rpx; }
.pl-2 { padding-left: 16rpx; }
.pl-3 { padding-left: 24rpx; }
.pl-4 { padding-left: 32rpx; }

.pr-0 { padding-right: 0; }
.pr-1 { padding-right: 8rpx; }
.pr-2 { padding-right: 16rpx; }
.pr-3 { padding-right: 24rpx; }
.pr-4 { padding-right: 32rpx; }

/* 阴影工具类 */
.shadow-sm {
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.shadow-md {
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.shadow-lg {
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
}

/* 圆角工具类 */
.rounded-none { border-radius: 0; }
.rounded-sm { border-radius: 8rpx; }
.rounded-md { border-radius: 16rpx; }
.rounded-lg { border-radius: 24rpx; }
.rounded-full { border-radius: 50%; }

/* 文字工具类 */
.text-xs { font-size: 20rpx; }
.text-sm { font-size: 24rpx; }
.text-base { font-size: 28rpx; }
.text-lg { font-size: 32rpx; }
.text-xl { font-size: 36rpx; }
.text-2xl { font-size: 40rpx; }

.font-light { font-weight: 300; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.text-gray-400 { color: #9ca3af; }
.text-gray-500 { color: #6b7280; }
.text-gray-600 { color: #4b5563; }
.text-gray-700 { color: #374151; }
.text-gray-800 { color: #1f2937; }
.text-gray-900 { color: #111827; }

.text-red-500 { color: #ef4444; }
.text-blue-500 { color: #3b82f6; }
.text-green-500 { color: #10b981; }
.text-yellow-500 { color: #f59e0b; }
.text-purple-500 { color: #8b5cf6; }
</style>
