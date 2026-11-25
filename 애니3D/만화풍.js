// GLB 사람(glb_사람.js 의 loadHuman 결과)을 만화풍으로: 셀 그림자(2~3단) 재료 + 먹선(뒷면 껍질, 뼈를 따라 함께 움직임)
//   사용: import { toonify, gradMap } from './만화풍.js';  toonify(human, { line: 0.0035 })
//   - 사진 같은 원래 겉면 그림(map)은 그대로 두고 빛만 2~3단으로 끊음 → 셀 애니 느낌
//   - 먹선은 이·눈·혀·입속·투명한 부분(머리카락 끝 등)에는 씌우지 않음 (입 벌릴 때 검은 덩어리, 머리 끝 검은 띠가 생겨서)
import * as THREE from 'three';

export function gradMap(steps = [110, 190, 255]) {
  const g = new THREE.DataTexture(new Uint8Array(steps), steps.length, 1, THREE.RedFormat);
  g.minFilter = g.magFilter = THREE.NearestFilter; g.needsUpdate = true; return g;
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
    om.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <project_vertex>', `transformed += normalize(objectNormal) * ${T.toFixed(6)};\n#include <project_vertex>`); };
    const sk = new THREE.SkinnedMesh(o.geometry, om); sk.bind(o.skeleton, o.bindMatrix);
    if (o.morphTargetInfluences) { sk.morphTargetInfluences = o.morphTargetInfluences; sk.morphTargetDictionary = o.morphTargetDictionary; }
    sk.frustumCulled = false; o.parent.add(sk); sk.position.copy(o.position); sk.quaternion.copy(o.quaternion); sk.scale.copy(o.scale);
  }
  return grad;
}
