(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const isSmall = window.innerWidth < 640;
  const reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.z = 16;

  // Phones get no antialiasing and a lower pixel ratio: the background is
  // decorative and this is by far the most expensive thing on the page.
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: !isSmall, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, isSmall ? 1 : 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const group = new THREE.Group();
  scene.add(group);

  const palette = [0x7c3aed, 0x22d3ee, 0xec4899];
  const geometries = [
    new THREE.IcosahedronGeometry(1, 0),
    new THREE.OctahedronGeometry(1, 0),
    new THREE.TorusGeometry(0.7, 0.25, 8, 16),
  ];
  // One material per colour, shared by every shape of that colour.
  const materials = palette.map(
    (color) => new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.35 })
  );

  const shapes = [];
  const SHAPE_COUNT = isSmall ? 12 : 24;
  for (let i = 0; i < SHAPE_COUNT; i++) {
    const mesh = new THREE.Mesh(geometries[i % geometries.length], materials[i % materials.length]);
    const radius = 9 + Math.random() * 10;
    const angle = Math.random() * Math.PI * 2;
    mesh.position.set(Math.cos(angle) * radius, (Math.random() - 0.5) * 14, Math.sin(angle) * radius - 6);
    mesh.scale.setScalar(0.5 + Math.random() * 1.4);
    mesh.userData.spin = { x: (Math.random() - 0.5) * 0.004, y: (Math.random() - 0.5) * 0.004 };
    mesh.userData.float = { speed: 0.2 + Math.random() * 0.4, offset: Math.random() * Math.PI * 2, baseY: mesh.position.y };
    group.add(mesh);
    shapes.push(mesh);
  }

  let mouseX = 0;
  let mouseY = 0;
  window.addEventListener(
    "mousemove",
    (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    },
    { passive: true }
  );

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      if (reducedMotion) renderer.render(scene, camera);
    }, 150);
  });

  const clock = new THREE.Clock();
  let frame = null;

  function animate() {
    frame = requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    shapes.forEach((mesh) => {
      mesh.rotation.x += mesh.userData.spin.x;
      mesh.rotation.y += mesh.userData.spin.y;
      const f = mesh.userData.float;
      mesh.position.y = f.baseY + Math.sin(t * f.speed + f.offset) * 0.6;
    });
    group.rotation.y += 0.0008;
    camera.position.x += (mouseX * 2 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 1.2 - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  }

  if (reducedMotion) {
    // A single still frame: same look, no animation.
    renderer.render(scene, camera);
    return;
  }

  // Stop rendering entirely while the tab is in the background.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      cancelAnimationFrame(frame);
      frame = null;
      clock.stop();
    } else if (frame === null) {
      clock.start();
      animate();
    }
  });

  animate();
})();
