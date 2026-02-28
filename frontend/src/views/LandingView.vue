<template>
  <div class="landing-page">
    <!-- Background -->
    <div class="landing-bg">
      <div class="bg-gradient-1"></div>
      <div class="bg-gradient-2"></div>
      <canvas ref="canvasRef" class="particle-canvas" />
    </div>

    <!-- Planet tooltip (shows on hover) -->
    <Transition name="tooltip-fade">
      <div v-if="hoveredMilestone" class="planet-tooltip" :style="tooltipStyle">
        <div class="tooltip-icon">{{ hoveredMilestone.icon }}</div>
        <div class="tooltip-content">
          <div class="tooltip-year">{{ hoveredMilestone.year }}</div>
          <div class="tooltip-name">{{ hoveredMilestone.name }}</div>
          <div class="tooltip-event">{{ hoveredMilestone.event }}</div>
        </div>
      </div>
    </Transition>

    <!-- Interactive character that avoids mouse -->
    <div
      ref="characterRef"
      class="landing-character"
      :class="{ 'caught': character.isCaught, 'escaping': character.isEscaping }"
      :style="{
        left: character.x + 'px',
        top: character.y + 'px',
        transform: `translate(-50%, -50%) rotate(${character.rotation}deg) scale(${character.scale})`,
        opacity: character.opacity
      }"
    >
      <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
        <!-- Body -->
        <circle cx="30" cy="36" r="18" :fill="character.isCaught ? '#ff6b6b' : '#1a1a2e'" stroke="#e0e7ff" stroke-width="2"/>
        <!-- Eyes -->
        <circle :cx="30 - character.eyeOffset" cy="32" r="3" fill="#1a1a2e"/>
        <circle :cx="30 + character.eyeOffset" cy="32" r="3" fill="#1a1a2e"/>
        <!-- Mouth -->
        <path
          :d="character.mouthPath"
          stroke="#e0e7ff"
          stroke-width="2"
          stroke-linecap="round"
          fill="none"
        />
        <!-- Shadow -->
        <ellipse cx="30" cy="56" rx="12" ry="3" fill="rgba(0,0,0,0.15)"/>
      </svg>

      <!-- Shadow underneath -->
      <div class="character-shadow"></div>
    </div>

    <!-- Navigation -->
    <nav class="landing-nav">
      <div class="nav-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="3" fill="url(#dotGrad)"/>
          <defs>
            <linearGradient id="dotGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#f97316"/>
              <stop offset="100%" stop-color="#8b5cf6"/>
            </linearGradient>
          </defs>
        </svg>
        <span>Workflow Manager</span>
      </div>
      <div class="nav-links">
        <a href="https://github.com/the-wayee" target="_blank" rel="noopener" class="nav-link github-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          关于我
        </a>
      </div>
    </nav>

    <!-- Main content -->
    <div class="landing-content">
      <div class="content-badge">
        <span class="badge-dot"></span>
        <span>让 AI 创作更简单</span>
      </div>

      <h1 class="content-title">
        <span class="title-line">把重复的工作交给代码</span>
        <span class="title-line title-highlight">把创意留给人类</span>
      </h1>

      <p class="content-desc">
        ComfyUI 工作流自动化管理平台。批量处理、定时执行、智能调度。
        <br>不用再守着屏幕等图，去做点有意思的事吧。
      </p>

      <div class="content-actions">
        <button class="action-btn primary" @click="enterDashboard">
          开始使用
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
        <a href="https://github.com/HEchooo/comfyUI-flow-task" target="_blank" rel="noopener" class="action-btn secondary">
          了解更多
        </a>
      </div>

      <!-- Mini feature preview -->
      <div class="content-features">
        <div class="feature-mini" v-for="f in miniFeatures" :key="f.icon">
          <span class="feature-mini-icon">{{ f.icon }}</span>
          <span>{{ f.text }}</span>
        </div>
      </div>
    </div>

    <!-- Hint -->
    <div class="landing-hint">
      <span>移动鼠标探索粒子，悬停行星发现人类进步</span>
    </div>

    <!-- Features section -->
    <section class="features-section">
      <div class="features-container">
        <h2 class="section-title">为什么选择我们</h2>

        <div class="feature-cards">
          <div class="feature-card" v-for="feature in features" :key="feature.title">
            <div class="feature-visual" :class="feature.color">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path v-if="feature.icon === 'template'" d="M20 7h-9m0 10h5m-5-4h-9m-9 4V7a3 3 0 0 1 3-3h13a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3h-3m-6 0h.01"/>
                <path v-else-if="feature.icon === 'clock'" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                <path v-else-if="feature.icon === 'layers'" d="M12 2L2 7l10 5 10-5-10 5 10 5-10-5z"/>
                <path v-else-if="feature.icon === 'zap'" d="M13 2L3 14h9l-1 8 10-13z"/>
              </svg>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-section">
      <div class="how-container">
        <h2 class="section-title">三步搞定</h2>
        <div class="how-steps">
          <div class="how-step" v-for="(step, index) in howSteps" :key="step.title">
            <div class="step-number">{{ index + 1 }}</div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA section -->
    <section class="cta-section">
      <div class="cta-container">
        <h2 class="cta-title">准备好了吗？</h2>
        <p class="cta-desc">加入我们，让 AI 成为你的创作助手</p>
        <button class="cta-btn" @click="enterDashboard">
          免费开始
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-left">
          <span class="footer-logo">Workflow Manager</span>
          <span class="footer-copy">© 2024</span>
        </div>
        <div class="footer-right">
          <a href="https://github.com/HEchooo/comfyUI-flow-task" target="_blank" rel="noopener" class="footer-link">GitHub</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useParticles } from '../composables/useParticles'

const router = useRouter()
const canvasRef = ref(null)
const characterRef = ref(null)
const isLoggedIn = Boolean(localStorage.getItem('task_manager_token'))

// Planet tooltip state
const hoveredMilestone = ref(null)
const tooltipPos = reactive({ x: 0, y: 0 })

const tooltipStyle = computed(() => ({
  left: tooltipPos.x + 'px',
  top: tooltipPos.y + 'px'
}))

const { init, destroy, refreshPlanets } = useParticles()

// Character state
const character = reactive({
  x: window.innerWidth / 2,
  y: window.innerHeight / 2,
  rotation: 0,
  eyeOffset: 0,
  mouthPath: 'M 25 40 Q 30 44 35 40',
  opacity: 0,
  scale: 1,
  isCaught: false,
  isEscaping: false,
  escapeSpeed: 0
})

// Mouse tracking for character interaction
let mouseX = 0
let mouseY = 0
let isMouseMoving = false
let mouseTimeout = null

// Feature data
const features = [
  {
    icon: 'template',
    title: '工作流管理',
    desc: '统一管理你的 AI 工作流，支持保存、复用和版本控制',
    color: 'orange'
  },
  {
    icon: 'clock',
    title: '定时调度',
    desc: '设置定时任务，到点自动执行。下班前设好，早上来看结果',
    color: 'purple'
  },
  {
    icon: 'layers',
    title: '批量处理',
    desc: '一次配置多个子任务，批量生成内容，效率翻倍',
    color: 'blue'
  },
  {
    icon: 'zap',
    title: '进度追踪',
    desc: '实时查看执行进度，每个节点的状态一目了然',
    color: 'green'
  }
]

const miniFeatures = [
  { icon: '⚡', text: '快' },
  { icon: '🎯', text: '准' },
  { icon: '🔄', text: '稳' }
]

const howSteps = [
  { title: '导入工作流', desc: '上传你的 ComfyUI API 格式工作流文件' },
  { title: '配置任务', desc: '设置子任务、选择模型、输入提示词和参数' },
  { title: '执行任务', desc: '一键执行或设置定时，自动批量生成内容' }
]

function enterDashboard() {
  if (isLoggedIn) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}

// Planet hover callbacks
function handlePlanetHover(milestone) {
  hoveredMilestone.value = milestone
}

function handlePlanetLeave() {
  hoveredMilestone.value = null
}

// Update tooltip position
function updateTooltipPosition(clientX, clientY) {
  tooltipPos.x = clientX + 20
  tooltipPos.y = clientY - 20

  // Keep tooltip in viewport
  const tooltipWidth = 280
  const tooltipHeight = 100

  if (tooltipPos.x + tooltipWidth > window.innerWidth) {
    tooltipPos.x = clientX - tooltipWidth - 20
  }
  if (tooltipPos.y + tooltipHeight > window.innerHeight) {
    tooltipPos.y = clientY - tooltipHeight - 20
  }
}

// Character animation - can be caught!
function updateCharacter() {
  const escapeRadius = 100 // Reduced -更容易被抓到
  const catchRadius = 80 // Increased -更容易被抓到
  const maxSpeed = 4 // Reduced - 逃跑更慢
  const catchChance = 0.15 // 15% chance - 大幅提高被抓概率

  // Calculate distance to mouse
  const dx = mouseX - character.x
  const dy = mouseY - character.y
  const distance = Math.sqrt(dx * dx + dy * dy)

  let velocityX = 0
  let velocityY = 0

  // Handle escaping state - 平滑逃跑
  if (character.isEscaping) {
    // Gradually slow down instead of sudden stop
    character.escapeSpeed *= 0.98
    if (character.escapeSpeed < 0.3) {
      character.isEscaping = false
      character.isCaught = false
    }

    // Continue moving in escape direction
    const escapeAngle = character.rotation * Math.PI / 180
    velocityX = Math.cos(escapeAngle) * character.escapeSpeed
    velocityY = Math.sin(escapeAngle) * character.escapeSpeed

    // Reset face gradually
    character.eyeOffset *= 0.95
    character.scale = 1 + Math.min(character.escapeSpeed / 15, 0.3)
  }
  // Check if caught (higher chance when very close)
  else if (distance < catchRadius && isMouseMoving && Math.random() < catchChance && !character.isCaught) {
    character.isCaught = true
    character.eyeOffset = 6
    character.mouthPath = 'M 20 35 Q 30 45 40 35' // Big smile
    character.scale = 1.25

    // After a short delay, escape smoothly
    setTimeout(() => {
      if (character.isCaught) {
        character.isCaught = false
        character.isEscaping = true
        character.escapeSpeed = 8 // Much slower escape - 平滑逃跑

        // Escape in random direction
        const escapeAngle = Math.random() * Math.PI * 2
        character.rotation = escapeAngle * (180 / Math.PI)
        character.eyeOffset = 8
        character.mouthPath = 'M 23 38 Q 30 30 37 38' // Surprised
      }
    }, 600) // Longer caught time
  }
  // Normal avoidance behavior - slower escape
  else if (distance < escapeRadius && isMouseMoving) {
    const angle = Math.atan2(dy, dx)
    const force = (escapeRadius - distance) / escapeRadius
    const speed = force * maxSpeed

    velocityX = -Math.cos(angle) * speed
    velocityY = -Math.sin(angle) * speed

    character.eyeOffset = 3
    character.mouthPath = 'M 23 38 Q 30 30 37 38'
    character.rotation = angle * (180 / Math.PI)
    character.scale = 1
  } else {
    // Wander slowly
    const time = Date.now() / 1000
    const wanderX = Math.sin(time * 0.4) * 0.8
    const wanderY = Math.cos(time * 0.3) * 0.8

    velocityX = wanderX
    velocityY = wanderY

    character.eyeOffset = Math.sin(time * 1.5) * 3
    character.mouthPath = 'M 25 42 Q 30 46 35 42'
    character.rotation = wanderX * 15
    character.scale = 1
  }

  // Update position
  character.x += velocityX
  character.y += velocityY

  // Keep in bounds (leave space for navigation bar at top)
  const navHeight = 80 // Account for fixed navigation bar
  const padding = 50
  character.x = Math.max(padding, Math.min(window.innerWidth - padding, character.x))
  character.y = Math.max(navHeight + padding, Math.min(window.innerHeight - padding, character.y))

  // Fade in on mount
  if (character.opacity < 1) {
    character.opacity += 0.02
  }

  requestAnimationFrame(updateCharacter)
}

function handleMouseMove(e) {
  mouseX = e.clientX
  mouseY = e.clientY
  isMouseMoving = true

  // Update tooltip position if hovering
  if (hoveredMilestone.value) {
    updateTooltipPosition(e.clientX, e.clientY)
  }

  clearTimeout(mouseTimeout)
  mouseTimeout = setTimeout(() => {
    isMouseMoving = false
  }, 500)
}

function handleClick(e) {
  const rect = characterRef.value.getBoundingClientRect()
  const charCenterX = rect.left + rect.width / 2
  const charCenterY = rect.top + rect.height / 2
  const dx = e.clientX - charCenterX
  const dy = e.clientY - charCenterY
  const distance = Math.sqrt(dx * dx + dy * dy)

  // Increased click range - 更容易点到
  if (distance < 120 && !character.isCaught && !character.isEscaping) {
    character.isCaught = true
    character.eyeOffset = 6
    character.mouthPath = 'M 20 35 Q 30 45 40 35'
    character.scale = 1.25

    setTimeout(() => {
      if (character.isCaught) {
        character.isCaught = false
        character.isEscaping = true
        character.escapeSpeed = 10 // Smooth escape, not teleport

        const angle = Math.atan2(dy, dx)
        character.rotation = angle * (180 / Math.PI)
        character.eyeOffset = 8
        character.mouthPath = 'M 23 38 Q 30 30 37 38'
      }
    }, 600)
  }
}

onMounted(() => {
  if (canvasRef.value) {
    init(canvasRef.value, {
      onPlanetHover: handlePlanetHover,
      onPlanetLeave: handlePlanetLeave
    })
  }

  // Initialize character position (below navigation bar)
  character.x = window.innerWidth * 0.75
  character.y = Math.max(150, window.innerHeight * 0.55) // Ensure below nav

  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('click', handleClick)

  // Start character animation loop
  updateCharacter()
})

onBeforeUnmount(() => {
  destroy()
  window.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('click', handleClick)
})
</script>

<style scoped>
@keyframes slideDownFade {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.landing-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
  overflow-x: hidden;
}

/* ── Background ── */
.landing-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.bg-gradient-1 {
  position: absolute;
  width: 600px;
  height: 600px;
  top: -200px;
  right: -100px;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.08) 0%, transparent 70%);
  border-radius: 50%;
}

.bg-gradient-2 {
  position: absolute;
  width: 500px;
  height: 500px;
  bottom: -100px;
  left: -100px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.06) 0%, transparent 70%);
  border-radius: 50%;
}

.particle-canvas {
  position: absolute;
  inset: 0;
  opacity: 1;
}

/* ── Planet Tooltip ── */
.planet-tooltip {
  position: fixed;
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  pointer-events: none;
  overflow: hidden;
}

.tooltip-icon {
  font-size: 28px;
  line-height: 1;
  padding: 14px 16px;
  background: #f5f5f5;
  border-right: 1px solid #e5e5e5;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 12px 16px 12px 0;
}

.tooltip-year {
  font-size: 10px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.tooltip-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.tooltip-event {
  font-size: 11px;
  color: #666;
}

.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

/* ── Character ── */
.landing-character {
  position: fixed;
  z-index: 150; /* Above navigation bar */
  cursor: pointer;
  transition: transform 0.1s ease-out;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
}

.landing-character.caught {
  transition: transform 0.15s ease-out;
  filter: drop-shadow(0 8px 24px rgba(255, 107, 107, 0.4));
}

.landing-character.escaping {
  transition: transform 0.05s ease-out;
}

.character-shadow {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 8px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  filter: blur(4px);
}

/* ── Navigation ── */
.landing-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  opacity: 0;
  animation: slideDownFade 0.6s ease-out forwards;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 20px;
  color: #1a1a2e;
  cursor: pointer;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-link {
  color: #64748b;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.2s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link:hover {
  color: #1a1a2e;
}

.github-link svg {
  transition: transform 0.2s ease;
}

.github-link:hover svg {
  transform: scale(1.1);
}

/* ── Main Content ── */
.landing-content {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 140px 32px 80px;
}

.content-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 9999px;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.2);
  color: #ea580c;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  margin-bottom: 24px;
  opacity: 0;
  animation: slideDownFade 0.6s ease-out 0.1s forwards;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f97316;
}

.content-title {
  font-size: clamp(36px, 5vw, 64px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: #1a1a2e;
  margin-bottom: 20px;
  opacity: 0;
  animation: slideDownFade 0.6s ease-out 0.2s forwards;
}

.title-line {
  display: block;
}

.title-highlight {
  color: #8b5cf6;
  position: relative;
}

.title-highlight::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #8b5cf6, #f97316);
  border-radius: 2px;
}

.content-desc {
  font-size: clamp(16px, 2vw, 18px);
  line-height: 1.7;
  color: #475569;
  margin-bottom: 32px;
  max-width: 600px;
  opacity: 0;
  animation: slideDownFade 0.6s ease-out 0.3s forwards;
}

.content-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  opacity: 0;
  animation: slideDownFade 0.6s ease-out 0.4s forwards;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  font-family: inherit;
}

.action-btn.primary {
  background: #1a1a2e;
  color: #fff;
}

.action-btn.primary:hover {
  background: #2d2d2d;
  transform: translateY(-1px);
}

.action-btn.secondary {
  background: #fff;
  color: #1a1a2e;
  border: 1px solid #e5e7eb;
}

.action-btn.secondary:hover {
  background: #f8fafc;
  border-color: #d1d5db;
}

.content-features {
  display: flex;
  gap: 16px;
  margin-top: 40px;
  opacity: 0;
  animation: slideDownFade 0.6s ease-out 0.5s forwards;
}

.feature-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 14px;
  color: #475569;
}

.feature-mini-icon {
  font-size: 16px;
}

/* ── Hint ── */
.landing-hint {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  z-index: 10;
}

/* ── Features Section ── */
.features-section {
  position: relative;
  z-index: 1;
  padding: 80px 32px;
  background: #fafafa;
}

.section-title {
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: #1a1a2e;
  text-align: center;
  margin-bottom: 48px;
}

.features-container {
  max-width: 1100px;
  margin: 0 auto;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.feature-card {
  padding: 28px;
  border-radius: 16px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.feature-card:hover {
  background: #fff;
  border-color: #d1d5db;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.feature-visual {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: #fff;
}

.feature-visual.orange { background: linear-gradient(135deg, #f97316, #fb923c); }
.feature-visual.purple { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.feature-visual.blue { background: linear-gradient(135deg, #3b82f6, #60a5fa); }
.feature-visual.green { background: linear-gradient(135deg, #10b981, #34d399); }

.feature-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.feature-desc {
  font-size: 14px;
  line-height: 1.6;
  color: #64748b;
}

/* ── How Section ── */
.how-section {
  position: relative;
  z-index: 1;
  padding: 80px 32px;
  background: #fafafa;
}

.how-container {
  max-width: 900px;
  margin: 0 auto;
}

.how-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 40px;
}

.how-step {
  text-align: center;
  padding: 24px;
}

.step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f97316, #8b5cf6);
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.step-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.step-desc {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}

/* ── CTA Section ── */
.cta-section {
  position: relative;
  z-index: 1;
  padding: 100px 32px;
  background: #1a1a2e;
  text-align: center;
}

.cta-container {
  max-width: 600px;
  margin: 0 auto;
}

.cta-title {
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
}

.cta-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 32px;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  border-radius: 12px;
  background: #fff;
  color: #1a1a2e;
  border: none;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cta-btn:hover {
  background: #fafafa;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.25);
}

/* ── Footer ── */
.landing-footer {
  position: relative;
  z-index: 1;
  padding: 24px 32px;
  background: #1a1a2e;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.footer-logo {
  font-weight: 700;
  color: #fff;
}

.footer-copy {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.footer-right {
  display: flex;
  gap: 24px;
}

.footer-link {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #fff;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .landing-nav {
    padding: 16px 20px;
  }

  .nav-logo span {
    display: none;
  }

  .landing-content {
    padding: 120px 20px 60px;
  }

  .content-actions {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }

  .content-features {
    flex-wrap: wrap;
  }

  .how-steps {
    grid-template-columns: 1fr;
  }

  .footer-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .planet-tooltip {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 10px 14px;
  }

  .tooltip-icon {
    font-size: 24px;
  }
}
</style>
