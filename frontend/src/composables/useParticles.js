// Three.js 懒加载，仅在 init() 调用时才动态导入，不影响主 bundle
let THREE = null

// Human progress milestones - our infinite planets of achievement
const MILESTONES = [
  // 计算机科学早期
  { name: "艾伦·图灵", event: "发明图灵机", year: 1936, icon: "🧮" },
  { name: "冯·诺依曼", event: "提出计算机架构", year: 1945, icon: "💻" },
  { name: "克劳德·香农", event: "信息论诞生", year: 1948, icon: "📡" },
  { name: "约翰·巴克斯", event: "发明Fortran语言", year: 1957, icon: "🔷" },

  // 太空探索
  { name: "尤里·加加林", event: "人类首次进入太空", year: 1961, icon: "🌟" },
  { name: "阿兰·谢帕德", event: "美国宇航员进入太空", year: 1961, icon: "🚀" },
  { name: "尼尔·阿姆斯特朗", event: "人类登月", year: 1969, icon: "🌙" },
  { name: "旅行者1号", event: "飞离太阳系", year: 2012, icon: "🛸" },
  { name: "NASA", event: "韦伯望远镜发射", year: 2021, icon: "🔭" },
  { name: "印度", event: "月船3号登月", year: 2023, icon: "🌕" },
  { name: "日本", event: "SLIM精准着陆月球", year: 2024, icon: "🎯" },

  // 互联网时代
  { name: "ARPANET", event: "互联网雏形诞生", year: 1969, icon: "🔗" },
  { name: "蒂姆·伯纳斯-李", event: "发明万维网", year: 1989, icon: "🌐" },
  { name: "林纳斯·托瓦兹", event: "创建Linux", year: 1991, icon: "🐧" },
  { name: "拉里·佩奇 & 谢尔盖·布林", event: "创立Google", year: 1998, icon: "🔍" },
  { name: "马克·扎克伯格", event: "创立Facebook", year: 2004, icon: "👥" },
  { name: "陈·杰克", event: "创立YouTube", year: 2005, icon: "📺" },
  { name: "杰克·多尔西", event: "创立Twitter", year: 2006, icon: "🐦" },

  // 移动革命
  { name: "摩托罗拉", event: "第一部手机", year: 1973, icon: "📞" },
  { name: "诺基亚", event: "连接人", year: 1998, icon: "📱" },
  { name: "史蒂夫·乔布斯", event: "发布iPhone", year: 2007, icon: "🍎" },
  { name: "安卓团队", event: "Android发布", year: 2008, icon: "🤖" },
  { name: "微信团队", event: "改变中国人生活", year: 2011, icon: "💬" },

  // AI革命
  { name: "马文·明斯基", event: "人工智能奠基", year: 1956, icon: "🧠" },
  { name: "杰弗里·辛顿", event: "深度学习突破", year: 2012, icon: "🔮" },
  { name: "DeepMind", event: "AlphaGo击败人类", year: 2016, icon: "⚫" },
  { name: "OpenAI", event: "GPT-3发布", year: 2020, icon: "📝" },
  { name: "OpenAI", event: "GPT-4发布", year: 2023, icon: "🧠" },
  { name: "OpenAI", event: "发布ChatGPT", year: 2022, icon: "🤖" },
  { name: "OpenAI", event: "Sora发布", year: 2024, icon: "🎬" },
  { name: "谷歌DeepMind", event: "AlphaFold预测蛋白质", year: 2021, icon: "🧬" },
  { name: "谷歌DeepMind", event: "AlphaFold3发布", year: 2024, icon: "🧬" },
  { name: "Midjourney", event: "AI图像生成革命", year: 2022, icon: "🎨" },
  { name: "Stability AI", event: "Stable Diffusion开源", year: 2022, icon: "✨" },
  { name: "Anthropic", event: "Claude发布", year: 2023, icon: "🦕" },

  // 区块链与金融
  { name: "中本聪", event: "发明比特币", year: 2008, icon: "₿" },
  { name: "Vitalik", event: "以太坊智能合约", year: 2015, icon: "💎" },
  { name: "NFT社区", event: "数字艺术品", year: 2021, icon: "🖼️" },

  // 生物技术
  { name: "沃森&克里克", event: "发现DNA双螺旋", year: 1953, icon: "🧬" },
  { name: "人类基因组计划", event: "完成基因测序", year: 2003, icon: "🧬" },
  { name: "华大基因", event: "基因测序普及", year: 2003, icon: "🔬" },
  { name: "Jennifer Doudna", event: "CRISPR基因编辑", year: 2012, icon: "✂️" },
  { name: "人类", event: "可控核聚变点火", year: 2022, icon: "⚡" },

  // 能源革命
  { name: "特斯拉", event: "Model S改变汽车", year: 2012, icon: "🚗" },
  { name: "比亚迪", event: "新能源汽车领先", year: 2022, icon: "🔋" },
  { name: "宁德时代", event: "电池技术突破", year: 2021, icon: "🔋" },
  { name: "隆基绿能", event: "光伏效率纪录", year: 2023, icon: "☀️" },

  // 机器人技术
  { name: "波士顿动力", event: "机器人后空翻", year: 2017, icon: "🤾" },
  { name: "特斯拉", event: "Optimus机器人", year: 2022, icon: "🤖" },
  { name: "Figure AI", event: "人形机器人工作", year: 2024, icon: "🧑‍🏭" },
  { name: "宇树科技", event: "机器狗量产", year: 2023, icon: "🐕" },

  // 航天突破
  { name: "伊隆·马斯克", event: "SpaceX成立", year: 2002, icon: "🚀" },
  { name: "伊隆·马斯克", event: "猎鹰9号可回收", year: 2015, icon: "🔄" },
  { name: "伊隆·马斯克", event: "星链卫星发射", year: 2019, icon: "📡" },
  { name: "Spacex", event: "星舰首飞", year: 2023, icon: "🛸" },
  { name: "中国航天", event: "天宫空间站建成", year: 2022, icon: "🏠" },
  { name: "中国航天", event: "嫦娥探月取样", year: 2020, icon: "🌙" },
  { name: "中国航天", event: "祝融号火星车", year: 2021, icon: "🔥" },
  { name: "蓝色起源", event: "太空旅游", year: 2021, icon: "🎢" },

  // 芯片技术
  { name: "英伟达", event: "GPU革命", year: 2020, icon: "🎮" },
  { name: "黄仁勋", event: "AI芯片霸主", year: 2023, icon: "💚" },
  { name: "台积电", event: "3nm工艺量产", year: 2023, icon: "⚡" },
  { name: "华为", event: "麒麟芯片回归", year: 2023, icon: "📱" },
  { name: "AMD", event: "锐龙处理器崛起", year: 2017, icon: "🔴" },

  // 脑机接口
  { name: "马斯克", event: "Neuralink人体试验", year: 2024, icon: "🧠" },
  { name: "BrainGate", event: "瘫痪患者用意念打字", year: 2021, icon: "⌨️" },

  // 量子计算
  { name: "Google", event: "量子霸权", year: 2019, icon: "⚛️" },
  { name: "IBM", event: "量子计算机商用", year: 2023, icon: "🔬" },
  { name: "中国科学家", event: "九章量子计算机", year: 2020, icon: "🎯" },

  // 材料科学
  { name: "杨培东", event: "纳米材料突破", year: 2003, icon: "🔬" },
  { name: "科学家", event: "石墨烯发现", year: 2004, icon: "⬛" },
  { name: "科学家", event: "常温超导突破", year: 2023, icon: "❄️" },

  // 通信技术
  { name: "摩托罗拉", event: "第一部商用手机", year: 1983, icon: "📱" },
  { name: "华为", event: "5G技术领先", year: 2019, icon: "5️⃣" },
  { name: "爱立信", event: "6G研发启动", year: 2023, icon: "6️⃣" },
  { name: "Starlink", event: "全球卫星互联网", year: 2023, icon: "🌍" },

  // 自动驾驶
  { name: "特斯拉", event: "FSD自动驾驶", year: 2020, icon: "🚗" },
  { name: "Waymo", event: "Robotaxi商用", year: 2023, icon: "🚕" },
  { name: "百度Apollo", event: "无人出租车运营", year: 2023, icon: "🇨🇳" },
  { name: "小鹏汽车", event: "城市NGP", year: 2023, icon: "🚙" },

  // 虚拟现实
  { name: "Oculus", event: "VR头显普及", year: 2016, icon: "🥽" },
  { name: "苹果", event: "Vision Pro发布", year: 2024, icon: "📱" },
  { name: "Meta", event: "元宇宙概念", year: 2021, icon: "🌐" },

  // 中国科技
  { name: "北斗卫星", event: "全球组网完成", year: 2020, icon: "🛰️" },
  { name: "中国高铁", event: "运营里程世界之最", year: 2023, icon: "🚄" },
  { name: "港珠澳大桥", event: "世纪工程通车", year: 2018, icon: "🌉" },
  { name: "大疆创新", event: "无人机全球领先", year: 2023, icon: "🚁" },
  { name: "TikTok", event: "风靡全球", year: 2020, icon: "🎵" },
  { name: "Temu", event: "电商出海", year: 2023, icon: "🛒" },
  { name: "Shein", event: "快时尚全球化", year: 2022, icon: "👗" },

  // 医疗突破
  { name: "BioNTech", event: "mRNA疫苗", year: 2020, icon: "💉" },
  { name: "科学家", event: "癌症免疫疗法", year: 2023, icon: "💊" },

  // 其他
  { name: "GitHub", event: "开源代码托管", year: 2008, icon: "🐙" },
  { name: "维基百科", event: "人类知识共享", year: 2001, icon: "📚" },
]

export function useParticles() {
  let scene, camera, renderer, points, planetsGroup, animationId
  let mouseX = 0
  let mouseY = 0
  let targetMouseX = 0
  let targetMouseY = 0
  // 延迟初始化，等待 THREE 加载后赋值
  let mouseWorldPos = null
  let raycaster = null
  let hoveredPlanet = null

  // Callback for planet hover
  let onPlanetHover = null
  let onPlanetLeave = null

  async function init(canvas, callbacks = {}) {
    // 首次调用时才加载 Three.js，后续复用已加载的模块
    if (!THREE) {
      THREE = await import('three')
    }
    // THREE 加载完毕后初始化依赖 THREE 的对象
    mouseWorldPos = new THREE.Vector3()
    raycaster = new THREE.Raycaster()

    onPlanetHover = callbacks.onPlanetHover
    onPlanetLeave = callbacks.onPlanetLeave

    const width = window.innerWidth
    const height = window.innerHeight

    /* ── Scene ── */
    scene = new THREE.Scene()

    /* ── Camera ── */
    camera = new THREE.PerspectiveCamera(60, width / height, 1, 2000)
    camera.position.z = 500

    /* ── Renderer ── */
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    /* ── Particles ── */
    const particleCount = 2000
    const positions = new Float32Array(particleCount * 3)
    const colors = new Float32Array(particleCount * 3)
    const velocities = new Float32Array(particleCount * 3)
    const baseSizes = new Float32Array(particleCount)
    const hoverStates = new Float32Array(particleCount)

    // Vibrant rainbow palette
    const palette = [
      new THREE.Color('#ff6b6b'),
      new THREE.Color('#feca57'),
      new THREE.Color('#48dbfb'),
      new THREE.Color('#ff9ff3'),
      new THREE.Color('#54a0ff'),
      new THREE.Color('#5f27cd'),
      new THREE.Color('#00d2d3'),
      new THREE.Color('#ff9f43'),
      new THREE.Color('#10ac84'),
      new THREE.Color('#ee5a24'),
      new THREE.Color('#0652DD'),
      new THREE.Color('#9980FA'),
      new THREE.Color('#D980FA'),
      new THREE.Color('#FDA7DF'),
      new THREE.Color('#ED4C67'),
    ]

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3
      positions[i3] = (Math.random() - 0.5) * 1400
      positions[i3 + 1] = (Math.random() - 0.5) * 900
      positions[i3 + 2] = (Math.random() - 0.5) * 700

      const color = palette[Math.floor(Math.random() * palette.length)]
      colors[i3] = color.r
      colors[i3 + 1] = color.g
      colors[i3 + 2] = color.b

      velocities[i3] = (Math.random() - 0.5) * 0.2
      velocities[i3 + 1] = (Math.random() - 0.5) * 0.2
      velocities[i3 + 2] = (Math.random() - 0.5) * 0.1

      baseSizes[i] = 4 + Math.random() * 4
      hoverStates[i] = 0
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('baseSize', new THREE.BufferAttribute(baseSizes, 1))
    geometry.setAttribute('hoverState', new THREE.BufferAttribute(hoverStates, 1))

    const material = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
        uMouseWorld: { value: new THREE.Vector3(9999, 9999, 9999) }
      },
      vertexShader: `
        attribute vec3 color;
        attribute float baseSize;
        attribute float hoverState;
        varying vec3 vColor;
        varying float vAlpha;
        varying float vHover;
        uniform float uTime;
        uniform float uPixelRatio;
        uniform vec3 uMouseWorld;

        void main() {
          vColor = color;
          vHover = hoverState;
          vec3 pos = position;

          float offset = length(pos) * 0.008;
          pos.x += sin(uTime * 0.25 + offset) * 3.0;
          pos.y += cos(uTime * 0.2 + offset * 1.2) * 3.0;
          pos.z += sin(uTime * 0.15 + offset * 0.8) * 2.0;

          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          float dist = -mvPosition.z;
          vAlpha = smoothstep(1500.0, 100.0, dist) * 0.9;

          float distToMouse = distance(pos, uMouseWorld);
          float hoverBoost = smoothstep(150.0, 0.0, distToMouse) * 8.0 * hoverState;
          float pulse = sin(offset * 2.0 + uTime * 1.5) * 0.3 + 1.0;
          float size = (baseSize + hoverBoost) * pulse * uPixelRatio * (350.0 / dist);

          gl_PointSize = size;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        varying float vHover;

        void main() {
          float d = length(gl_PointCoord - vec2(0.5));
          if (d > 0.5) discard;

          float glow = 1.0 - smoothstep(0.0, 0.5, d);
          glow = pow(glow, 1.2);

          vec3 finalColor = mix(vColor, vec3(1.0), vHover * 0.4);
          float finalAlpha = glow * vAlpha * (0.7 + vHover * 0.3);

          gl_FragColor = vec4(finalColor, finalAlpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })

    points = new THREE.Points(geometry, material)
    points._velocities = velocities
    scene.add(points)

    /* ── Planets (Milestones) ── */
    createPlanets()

    /* ── Events ── */
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('resize', onResize)

    animate()
  }

  function createPlanets() {
    planetsGroup = new THREE.Group()

    // Randomly select 6-9 milestones to display
    const displayCount = 6 + Math.floor(Math.random() * 4)
    const shuffled = [...MILESTONES].sort(() => Math.random() - 0.5)
    const selectedMilestones = shuffled.slice(0, displayCount)

    // Planet colors
    const planetColors = [
      new THREE.Color('#ff6b6b'),
      new THREE.Color('#feca57'),
      new THREE.Color('#48dbfb'),
      new THREE.Color('#ff9ff3'),
      new THREE.Color('#54a0ff'),
      new THREE.Color('#5f27cd'),
      new THREE.Color('#00d2d3'),
      new THREE.Color('#10ac84'),
    ]

    selectedMilestones.forEach((milestone, index) => {
      const planetGroup = new THREE.Group()

      // Planet sphere with glow
      const planetGeometry = new THREE.SphereGeometry(12 + Math.random() * 8, 32, 32)
      const planetColor = planetColors[index % planetColors.length]

      const planetMaterial = new THREE.ShaderMaterial({
        uniforms: {
          uColor: { value: planetColor },
          uTime: { value: 0 },
          uHover: { value: 0 }
        },
        vertexShader: `
          varying vec3 vNormal;
          varying vec2 vUv;
          uniform float uHover;

          void main() {
            vNormal = normalize(normalMatrix * normal);
            vUv = uv;
            vec3 pos = position;
            pos += normal * uHover * 2.0;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 uColor;
          uniform float uTime;
          uniform float uHover;
          varying vec3 vNormal;
          varying vec2 vUv;

          void main() {
            float fresnel = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.0);
            vec3 glow = uColor * (0.6 + fresnel * 0.4 + uHover * 0.5);

            // Add subtle pattern
            float pattern = sin(vUv.y * 20.0 + uTime) * 0.05 + 0.95;

            gl_FragColor = vec4(glow * pattern, 0.85);
          }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      })

      const planet = new THREE.Mesh(planetGeometry, planetMaterial)
      planetGroup.add(planet)

      // Orbit ring
      const ringGeometry = new THREE.RingGeometry(18, 19, 64)
      const ringMaterial = new THREE.ShaderMaterial({
        uniforms: {
          uColor: { value: planetColor },
          uTime: { value: 0 }
        },
        vertexShader: `
          varying vec2 vUv;
          void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 uColor;
          uniform float uTime;
          varying vec2 vUv;

          void main() {
            float angle = atan(vUv.y - 0.5, vUv.x - 0.5);
            float alpha = 0.3 + sin(angle * 8.0 + uTime * 2.0) * 0.2;
            gl_FragColor = vec4(uColor, alpha);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      })

      const ring = new THREE.Mesh(ringGeometry, ringMaterial)
      ring.rotation.x = Math.random() * 0.5
      ring.rotation.y = Math.random() * 0.5
      planetGroup.add(ring)

      // Position in 3D space
      const angle = (index / displayCount) * Math.PI * 2 + Math.random() * 0.5
      const radius = 250 + Math.random() * 200
      planetGroup.position.x = Math.cos(angle) * radius
      planetGroup.position.y = (Math.random() - 0.5) * 300
      planetGroup.position.z = Math.sin(angle) * radius * 0.5

      // Store milestone data
      planetGroup.userData = {
        milestone,
        planet,
        ring,
        baseY: planetGroup.position.y,
        orbitSpeed: 0.0003 + Math.random() * 0.0005,
        orbitAngle: angle,
        orbitRadius: radius
      }

      planetsGroup.add(planetGroup)
    })

    scene.add(planetsGroup)
  }

  function onMouseMove(event) {
    targetMouseX = (event.clientX / window.innerWidth - 0.5) * 2
    targetMouseY = (event.clientY / window.innerHeight - 0.5) * 2
    updateMouseWorldPosition(event.clientX, event.clientY)
    checkPlanetHover(event.clientX, event.clientY)
  }

  function updateMouseWorldPosition(clientX, clientY) {
    if (!camera || !points) return

    const mouse = new THREE.Vector2(
      (clientX / window.innerWidth) * 2 - 1,
      -(clientY / window.innerHeight) * 2 + 1
    )

    raycaster.setFromCamera(mouse, camera)
    const planeZ = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0)
    raycaster.ray.intersectPlane(planeZ, mouseWorldPos)
  }

  function checkPlanetHover(clientX, clientY) {
    if (!planetsGroup) return

    const mouse = new THREE.Vector2(
      (clientX / window.innerWidth) * 2 - 1,
      -(clientY / window.innerHeight) * 2 + 1
    )

    raycaster.setFromCamera(mouse, camera)

    // Check intersection with planet spheres
    const planetMeshes = []
    planetsGroup.children.forEach(group => {
      if (group.userData.planet) {
        planetMeshes.push(group.userData.planet)
      }
    })

    const intersects = raycaster.intersectObjects(planetMeshes)

    if (intersects.length > 0) {
      const intersectedPlanet = intersects[0].object
      const planetGroup = intersectedPlanet.parent

      if (hoveredPlanet !== planetGroup) {
        // Leave previous planet
        if (hoveredPlanet && onPlanetLeave) {
          onPlanetLeave()
        }

        // Enter new planet
        hoveredPlanet = planetGroup
        if (onPlanetHover) {
          onPlanetHover(planetGroup.userData.milestone)
        }
      }
    } else {
      if (hoveredPlanet && onPlanetLeave) {
        onPlanetLeave()
      }
      hoveredPlanet = null
    }
  }

  function onResize() {
    if (!camera || !renderer) return
    const width = window.innerWidth
    const height = window.innerHeight
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }

  let clock = null

  function animate() {
    if (!clock) clock = new THREE.Clock()
    animationId = requestAnimationFrame(animate)

    const elapsed = clock.getElapsedTime()

    /* ── Update particles ── */
    if (points?.material?.uniforms?.uTime) {
      points.material.uniforms.uTime.value = elapsed
      points.material.uniforms.uMouseWorld.value = mouseWorldPos
    }

    if (points) {
      const positions = points.geometry.attributes.position.array
      const velocities = points._velocities
      const hoverStates = points.geometry.attributes.hoverState.array
      const hoverRadius = 120

      for (let i = 0; i < positions.length / 3; i++) {
        const i3 = i * 3

        positions[i3] += velocities[i3]
        positions[i3 + 1] += velocities[i3 + 1]
        positions[i3 + 2] += velocities[i3 + 2]

        if (positions[i3] > 700) positions[i3] = -700
        if (positions[i3] < -700) positions[i3] = 700
        if (positions[i3 + 1] > 450) positions[i3 + 1] = -450
        if (positions[i3 + 1] < -450) positions[i3 + 1] = 450
        if (positions[i3 + 2] > 350) positions[i3 + 2] = -350
        if (positions[i3 + 2] < -350) positions[i3 + 2] = 350

        const dx = positions[i3] - mouseWorldPos.x
        const dy = positions[i3 + 1] - mouseWorldPos.y
        const dz = positions[i3 + 2] - mouseWorldPos.z
        const distToMouse = Math.sqrt(dx * dx + dy * dy + dz * dz)

        const targetHover = distToMouse < hoverRadius ? 1.0 : 0.0
        hoverStates[i] += (targetHover - hoverStates[i]) * 0.08
      }

      points.geometry.attributes.position.needsUpdate = true
      points.geometry.attributes.hoverState.needsUpdate = true

      points.rotation.y += 0.0003
      points.rotation.x += 0.00015
    }

    /* ── Update planets ── */
    if (planetsGroup) {
      planetsGroup.children.forEach(group => {
        const data = group.userData

        // Orbit animation
        data.orbitAngle += data.orbitSpeed
        group.position.x = Math.cos(data.orbitAngle) * data.orbitRadius
        group.position.z = Math.sin(data.orbitAngle) * data.orbitRadius * 0.5

        // Float animation
        group.position.y = data.baseY + Math.sin(elapsed * 0.5 + data.orbitAngle) * 10

        // Rotate ring
        if (data.ring) {
          data.ring.rotation.z += 0.002
        }

        // Update shader uniforms
        if (data.planet?.material?.uniforms) {
          data.planet.material.uniforms.uTime.value = elapsed
          const targetHover = group === hoveredPlanet ? 1.0 : 0.0
          data.planet.material.uniforms.uHover.value += (targetHover - data.planet.material.uniforms.uHover.value) * 0.1
        }
        if (data.ring?.material?.uniforms) {
          data.ring.material.uniforms.uTime.value = elapsed
        }
      })

      planetsGroup.rotation.y += 0.0002
    }

    /* ── Smooth mouse parallax ── */
    mouseX += (targetMouseX - mouseX) * 0.04
    mouseY += (targetMouseY - mouseY) * 0.04
    camera.position.x = mouseX * 80
    camera.position.y = -mouseY * 50
    camera.lookAt(scene.position)

    renderer.render(scene, camera)
  }

  function destroy() {
    if (animationId) cancelAnimationFrame(animationId)
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('resize', onResize)
    if (points) {
      points.geometry.dispose()
      points.material.dispose()
    }
    if (planetsGroup) {
      planetsGroup.children.forEach(group => {
        if (group.userData.planet) {
          group.userData.planet.geometry.dispose()
          group.userData.planet.material.dispose()
        }
        if (group.userData.ring) {
          group.userData.ring.geometry.dispose()
          group.userData.ring.material.dispose()
        }
      })
    }
    if (renderer) {
      renderer.dispose()
    }
    scene = null
    camera = null
    renderer = null
    points = null
    planetsGroup = null
  }

  return { init, destroy, refreshPlanets: createPlanets }
}
