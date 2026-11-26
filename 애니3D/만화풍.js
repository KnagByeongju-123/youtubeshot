// GLB 사람(glb_사람.js 의 loadHuman 결과)을 만화풍으로: 셀 그림자(2~3단) 재료 + 먹선(뒷면 껍질, 뼈를 따라 함께 움직임)
//   사용: import { toonify, gradMap } from './만화풍.js';  toonify(human, { line: 0.0035 })
//   - 사진 같은 원래 겉면 그림(map)은 그대로 두고 빛만 2~3단으로 끊음 → 셀 애니 느낌
//   - 먹선은 입 모양으로 움직이는 입술·입속, 이·눈·혀·입속·투명한 부분(머리카락 끝 등)에는 씌우지 않음 (입 벌릴 때 검은 덩어리, 머리 끝 검은 띠가 생겨서)
import * as THREE from 'three';

export function gradMap(steps = [110, 190, 255]) {
  const g = new THREE.DataTexture(new Uint8Array(steps), steps.length, 1, THREE.RedFormat);
  g.minFilter = g.magFilter = THREE.NearestFilter; g.needsUpdate = true; return g;
}

// 입 모양 움직임 크기로 먹선 굵기 배율(0~1)을 점마다 정해 geometry 의 olw 로 넣음, 입 모양이 없으면 null
function mouthMask(o, cut) {
  const dict = o.morphTargetDictionary, mp = o.geometry.morphAttributes && o.geometry.morphAttributes.position;
  if (!dict || !mp) return null;
  const ids = Object.entries(dict).filter(([k]) => /mouth/i.test(k)).map(([, v]) => v);
  if (!ids.length) return null;
  const n = o.geometry.attributes.position.count, w = new Float32Array(n).fill(1);
  for (const id of ids) { const a = mp[id]; if (!a) continue;
    for (let i = 0; i < n; i++) { const d = Math.hypot(a.getX(i), a.getY(i), a.getZ(i)); w[i] = Math.min(w[i], Math.max(0, 1 - d / cut)); } }
  if (!w.some((x) => x < 1)) return null;
  o.geometry.setAttribute('olw', new THREE.BufferAttribute(w, 1)); return true;
}

export function toonify(human, opts = {}) {
  const grad = opts.grad || gradMap();
  const skip = /teeth|tooth|eye|lash|tongue|mouth/i;
  const list = []; human.scene.traverse((o) => { if (o.isMesh) list.push(o); });
  for (const o of list) {
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const nm = mats.map((m) => new THREE.MeshToonMaterial({ map: m.map || null, color: m.color ? m.color.clone() : 0xffffff, gradientMap: grad,
      transparent: m.transparent, alphaTest: m.alphaTest, side: m.side, opacity: m.opacity }));
    o.material = Array.isArray(o.material) ? nm : nm[0];
    if (skip.test(o.name) || mats.some((m) => m.transparent) || !o.isSkinnedMesh) continue;
    const om = new THREE.MeshBasicMaterial({ color: opts.color || 0x2a2026, side: THREE.BackSide });
    const T = (opts.line || 0.0035) / human.scale;          // 선 굵기(m)를 모델 단위로
    // 입 모양(Mouth…)으로 움직이는 점(입술·입속)에는 먹선을 안 씌움 — 입을 벌리면 아랫입술 속이 검게 보여서 (사용자 지적 2026-11-26)
    const mouthW = mouthMask(o, opts.mouthCut || 0.004 / human.scale);
    om.onBeforeCompile = (sh) => {
      if (mouthW) sh.vertexShader = 'attribute float olw;\n' + sh.vertexShader;
      sh.vertexShader = sh.vertexShader.replace('#include <project_vertex>', `transformed += normalize(objectNormal) * ${T.toFixed(6)}${mouthW ? ' * olw' : ''};\n#include <project_vertex>`); };
    const sk = new THREE.SkinnedMesh(o.geometry, om); sk.bind(o.skeleton, o.bindMatrix);
    if (o.morphTargetInfluences) { sk.morphTargetInfluences = o.morphTargetInfluences; sk.morphTargetDictionary = o.morphTargetDictionary; }
    sk.frustumCulled = false; o.parent.add(sk); sk.position.copy(o.position); sk.quaternion.copy(o.quaternion); sk.scale.copy(o.scale);
  }
  return grad;
}
