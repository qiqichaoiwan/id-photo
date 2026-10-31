<template><view class="page"><InlineState v-if="loading" kind="loading" title="正在查询订单" description="请稍候" /><InlineState v-else-if="!order" kind="error" title="订单暂不可用" description="请稍后重新查询" action-text="重新查询" @action="load" /><view v-else class="card"><view class="title">{{ statusText(order.status) }}</view><view class="row"><text>套餐</text><text>{{ order.plan_name }}</text></view><view class="row"><text>金额</text><text>¥{{ price(order.price_fen) }}</text></view><view class="row"><text>订单编号</text><text>{{ order.order_no }}</text></view><view class="row"><text>创建时间</text><text>{{ date(order.created_at) }}</text></view><view v-if="order.expires_at" class="row"><text>本单发放后的有效期</text><text>{{ date(order.expires_at) }}</text></view><view v-if="order.status === 'pending'" class="note">支付结果确认中，请勿重复付款。微信支付已取消时也需要先查询订单状态。</view><view v-if="order.review_needed" class="note">订单信息正在人工核对。</view><view class="refresh" @click="refresh(false)">向微信查询订单状态</view></view></view></template>
<script lang="ts">
import Vue from 'vue'; import { Component } from 'vue-property-decorator';
import InlineState from '@/components/InlineState.vue'; import { getMembershipOrder, refreshMembershipOrder, MembershipOrder, formatFen, formatMemberDate } from '@/api/membership';
@Component({ components: { InlineState } }) export default class Order extends Vue {
  orderNo=''; order:MembershipOrder|null=null; loading=true;
  onLoad(options:any){ this.orderNo=options.order_no||''; this.load(); }
  async load(){
    this.loading=true;
    try { this.order=await getMembershipOrder(this.orderNo); }
    catch (_) { this.order=null; }
    finally { this.loading=false; }
    if(this.order && this.order.status==='pending') this.refresh(true);
  }
  async refresh(silent=false){
    if(!this.orderNo || this.loading)return;
    this.loading=true;
    try { this.order=await refreshMembershipOrder(this.orderNo); }
    catch (_) { if(!silent) uni.showToast({title:'订单确认中，请稍后重试',icon:'none'}); }
    finally { this.loading=false; }
  }
  price(value:number){return formatFen(value);} date(value:string){return formatMemberDate(value);}
  statusText(value:string){return ({paid:'订单已完成',pending:'订单确认中',cancelled:'订单已取消',closed:'订单已关闭',failed:'订单未完成',refunded:'订单已退款'} as any)[value] || '订单处理中';}
}
</script>
<style lang="scss" scoped>@import '@/assets/design-tokens.scss'; .page{min-height:100vh;background:$page;padding:28rpx;box-sizing:border-box}.card{@include card;padding:32rpx;color:$muted;font-size:26rpx}.title{font-size:36rpx;font-weight:700;color:$ink;margin:12rpx 0 25rpx}.row{display:flex;justify-content:space-between;gap:20rpx;border-top:1rpx solid $border;padding:24rpx 0}.row text:last-child{color:$ink;text-align:right;word-break:break-all}.note{line-height:1.6}.refresh{color:$brand;margin-top:24rpx;text-align:center;padding:20rpx}</style>
