"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface ThreeRadarGlobeProps {
  matchScore?: number;
  opportunityScore?: number;
}

export const ThreeRadarGlobe: React.FC<ThreeRadarGlobeProps> = ({
  matchScore = 94,
  opportunityScore = 97,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 280;
    const height = container.clientHeight || 280;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 5.2;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 1. Holographic Wireframe Core Sphere
    const sphereGeo = new THREE.IcosahedronGeometry(1.6, 2);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphere);

    // 2. Inner Glowing Core Orb
    const innerGeo = new THREE.SphereGeometry(1.1, 24, 24);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: false,
      transparent: true,
      opacity: 0.15,
    });
    const innerCore = new THREE.Mesh(innerGeo, innerMat);
    scene.add(innerCore);

    // 3. Orbital Radar Rings
    const ringGeo = new THREE.RingGeometry(2.1, 2.14, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const ring1 = new THREE.Mesh(ringGeo, ringMat);
    ring1.rotation.x = Math.PI / 3;
    scene.add(ring1);

    const ring2Geo = new THREE.RingGeometry(2.3, 2.33, 64);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.35,
    });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.y = Math.PI / 4;
    ring2.rotation.x = -Math.PI / 6;
    scene.add(ring2);

    // 4. Opportunity Satellites / Nodes
    const nodeGeo = new THREE.SphereGeometry(0.08, 12, 12);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const nodes: THREE.Mesh[] = [];
    for (let i = 0; i < 6; i++) {
      const node = new THREE.Mesh(nodeGeo, nodeMat);
      const theta = (i / 6) * Math.PI * 2;
      node.position.set(Math.cos(theta) * 1.8, Math.sin(theta) * 1.8 * 0.4, Math.sin(theta) * 1.4);
      scene.add(node);
      nodes.push(node);
    }

    let frameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      sphere.rotation.y = time * 0.2;
      sphere.rotation.x = time * 0.1;
      innerCore.rotation.y = -time * 0.15;

      ring1.rotation.z = time * 0.3;
      ring2.rotation.z = -time * 0.25;

      nodes.forEach((node, i) => {
        const theta = (i / 6) * Math.PI * 2 + time * 0.4;
        node.position.x = Math.cos(theta) * 1.9;
        node.position.z = Math.sin(theta) * 1.9;
        node.position.y = Math.sin(time + i) * 0.3;
      });

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(frameId);
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      sphereGeo.dispose();
      sphereMat.dispose();
      innerGeo.dispose();
      innerMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      ring2Geo.dispose();
      ring2Mat.dispose();
      nodeGeo.dispose();
      nodeMat.dispose();
      renderer.dispose();
    };
  }, [matchScore, opportunityScore]);

  return (
    <div className="relative flex flex-col items-center justify-center">
      <div ref={mountRef} className="w-64 h-64 cursor-grab active:cursor-grabbing" />
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-3xl font-heading font-bold text-white tracking-wider">
          {matchScore}%
        </span>
        <span className="text-xs uppercase tracking-widest text-cyan-400 font-mono font-medium">
          Signal Match
        </span>
      </div>
    </div>
  );
};
