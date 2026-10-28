<template>
  <div class="init-page">
    <div class="init-grid" aria-hidden="true"></div>
    <section class="init-panel">
      <div class="init-tag"><span></span>CYBERRANGE / INIT</div>
      <h1>初始化界面</h1>
      <p class="init-subtitle">网络安全实战靶场与流量分析学习平台</p>
      <div class="init-rule"></div>
      <div class="init-status"><i></i>页面内容暂定</div>
      <p class="init-note">当前为初始化页面占位，正式内容后续补充。</p>
      <router-link to="/overview" class="init-link">进入总览 <span>→</span></router-link>
    </section>
  </div>
</template>

<style scoped>
.init-page {
  position: relative;
  display: grid;
  place-items: center;
  min-height: calc(100vh - 145px);
  padding: 48px 24px;
  overflow: hidden;
}
.init-grid {
  position: absolute;
  inset: 0;
  opacity: 0.55;
  background-image:
    linear-gradient(rgba(var(--green-rgb), 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--green-rgb), 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 68% 72% at 50% 46%, #000 20%, transparent 82%);
  pointer-events: none;
}
.init-page::before {
  content: '';
  position: absolute;
  width: min(820px, 84vw);
  height: min(480px, 52vw);
  border-radius: 50%;
  background: rgba(var(--green-rgb), 0.08);
  filter: blur(110px);
  pointer-events: none;
}
.init-panel {
  position: relative;
  z-index: 1;
  width: min(100%, 920px);
  padding: 74px 72px 68px;
  border: 1px solid var(--line2);
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgba(var(--green-rgb), 0.045), transparent 38%),
    var(--panel);
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.35);
}
.init-panel::before,
.init-panel::after {
  content: '';
  position: absolute;
  width: 54px;
  height: 54px;
  border-color: var(--green);
  opacity: 0.65;
  pointer-events: none;
}
.init-panel::before {
  top: 14px;
  left: 14px;
  border-top: 1px solid;
  border-left: 1px solid;
}
.init-panel::after {
  right: 14px;
  bottom: 14px;
  border-right: 1px solid;
  border-bottom: 1px solid;
}
.init-tag {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 22px;
  color: var(--green);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 2px;
}
.init-tag span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 14px var(--green);
}
.init-panel h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(42px, 7vw, 76px);
  line-height: 1.05;
  letter-spacing: 0.04em;
}
.init-subtitle {
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.8;
}
.init-rule {
  width: 120px;
  height: 1px;
  margin: 36px 0 28px;
  background: linear-gradient(90deg, var(--green), transparent);
}
.init-status {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--text);
  font-size: 14px;
  font-weight: 700;
}
.init-status i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--amber);
  box-shadow: 0 0 10px rgba(var(--amber-rgb), 0.75);
}
.init-note {
  max-width: 560px;
  margin: 12px 0 34px;
  color: var(--dim);
  font-size: 13px;
  line-height: 1.8;
}
.init-link {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  padding: 11px 18px;
  border: 1px solid var(--green);
  border-radius: 6px;
  color: var(--green);
  font-size: 14px;
  font-weight: 700;
  transition: 0.18s ease;
}
.init-link span {
  font-family: var(--mono);
  font-size: 18px;
  line-height: 1;
  transition: transform 0.18s ease;
}
.init-link:hover {
  background: rgba(var(--green-rgb), 0.08);
  box-shadow: 0 0 20px rgba(var(--green-rgb), 0.12);
}
.init-link:hover span {
  transform: translateX(4px);
}
@media (max-width: 640px) {
  .init-page {
    min-height: calc(100vh - 132px);
    padding: 24px 14px;
  }
  .init-panel {
    padding: 52px 26px 46px;
  }
  .init-subtitle {
    font-size: 14px;
  }
}
</style>
