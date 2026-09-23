(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.z = 16;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const group = new THREE.Group();
  scene.add(group);

  const palette = [0x7c3aed, 0x22d3ee, 0xec4899];
  const geometries = [
    new THREE.IcosahedronGeometry(1, 0),
    new THREE.OctahedronGeometry(1, 0),
    new THREE.TorusGeometry(0.7, 0.25, 8, 16),
  ];

  const shapes = [];
  const SHAPE_COUNT = window.innerWidth < 640 ? 14 : 26;
  for (let i = 0; i < SHAPE_COUNT; i++) {
    const geo = geometries[i % geometries.length];
    const mat = new THREE.MeshBasicMaterial({
      color: palette[i % palette.length],
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const mesh = new THREE.Mesh(geo, mat);
    const radius = 9 + Math.random() * 10;
    const angle = Math.random() * Math.PI * 2;
    mesh.position.set(
      Math.cos(angle) * radius,
      (Math.random() - 0.5) * 14,
      Math.sin(angle) * radius - 6
    );
    const scale = 0.5 + Math.random() * 1.4;
    mesh.scale.setScalar(scale);
    mesh.userData.spin = {
      x: (Math.random() - 0.5) * 0.004,
      y: (Math.random() - 0.5) * 0.004,
    };
    mesh.userData.float = {
      speed: 0.2 + Math.random() * 0.4,
      offset: Math.random() * Math.PI * 2,
      baseY: mesh.position.y,
    };
    group.add(mesh);
    shapes.push(mesh);
  }

  let mouseX = 0;
  let mouseY = 0;
  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
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

  animate();
})();
