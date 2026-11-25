// 일반 GLB 사람 모델(자동 리깅 + glb_다시리깅.py 로 손가락까지 다시 리깅한 것)을 VRM 처럼 다루는 도구
//   - 뼈마다 '정규화된 대리인'을 만들어, VRM 과 같은 뼈 이름(leftUpperArm, leftIndexProximal …)·같은 회전 약속으로 움직임
//     (쉬는 자세에서 모든 뼈 방향이 세계 축과 같다고 보고 회전함: x축 회전 = 앞뒤로 흔들기, z축 = 옆으로 들기)
//   - 손가락 굽히기: curl(이름, 각도) — 손가락이 손바닥 쪽으로 굽음
//   - 표정: 모델의 모양 키(Blink, MouthOpen …)를 VRM 표정 이름(blink, aa …)으로 연결
//   사용: const human = await loadHuman(loader, '../models/glb/announcer_rig.glb', { height: 1.62 }); scene.add(human.scene)
//         human.humanoid.getNormalizedBoneNode('leftUpperArm').rotation.x = -1;  human.curl('leftIndex', 1.2);  human.update()
import * as THREE from 'three';

// VRM 이름 → 모델 뼈 이름 후보 (three.js 는 이름의 '.' 을 지움). 두 가지 이름 방식: 'UpperArm.L' 식 / 'LeftUpperArm' 식
const BASE = {
  hips: ['Hips'], spine: ['Spine'], chest: ['Chest'], neck: ['Neck'], head: ['Head'], jaw: ['Jaw'],
  leftShoulder: ['ShoulderL', 'LeftShoulder'], rightShoulder: ['ShoulderR', 'RightShoulder'],
  leftUpperArm: ['UpperArmL', 'LeftUpperArm'], leftLowerArm: ['ForeArmL', 'LeftForeArm'], leftHand: ['HandL', 'LeftHand'],
  rightUpperArm: ['UpperArmR', 'RightUpperArm'], rightLowerArm: ['ForeArmR', 'RightForeArm'], rightHand: ['HandR', 'RightHand'],
  leftUpperLeg: ['UpperLegL', 'LeftUpperLeg'], leftLowerLeg: ['LowerLegL', 'LeftLowerLeg'], leftFoot: ['FootL', 'LeftFoot'], leftToes: ['ToeL', 'LeftToe'],
  rightUpperLeg: ['UpperLegR', 'RightUpperLeg'], rightLowerLeg: ['LowerLegR', 'RightLowerLeg'], rightFoot: ['FootR', 'RightFoot'], rightToes: ['ToeR', 'RightToe'],
};
const FINGERS = { Thumb: ['Metacarpal', 'Proximal', 'Distal'], Index: ['Proximal', 'Intermediate', 'Distal'], Middle: ['Proximal', 'Intermediate', 'Distal'],
  Ring: ['Proximal', 'Intermediate', 'Distal'], Little: ['Proximal', 'Intermediate', 'Distal'] };
const NAME = { ...BASE };
for (const [side, S, Side] of [['left', 'L', 'Left'], ['right', 'R', 'Right']])
  for (const [f, parts] of Object.entries(FINGERS)) parts.forEach((p, k) => { NAME[`${side}${f}${p}`] = [`${f}${k + 1}${S}`, `${Side}${f}${k + 1}`]; });
const EXPR = { blink: 'Blink', aa: 'MouthOpen', ih: 'MouthWide', ou: 'MouthRound', ee: 'MouthWide', oh: 'MouthRound' };

export function loadHuman(loader, url, opts = {}) {
  return new Promise((ok, bad) => loader.load(url, (gltf) => {
    const root = gltf.scene; root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(root), hgt = box.max.y - box.min.y;
    const k = (opts.height || 1.62) / hgt;                    // 키를 실제 크기로
    root.scale.setScalar(k); root.position.y = -box.min.y * k;
    const holder = new THREE.Group(); holder.add(root); holder.updateMatrixWorld(true);
    const prox = {};
    for (const [n, cands] of Object.entries(NAME)) {
      let b = null; for (const c of cands) { b = root.getObjectByName(c); if (b) break; }
      if (!b || !b.isBone) continue;
      const Pw = b.parent.getWorldQuaternion(new THREE.Quaternion());
      prox[n] = { b, rest: b.quaternion.clone(), restPos: b.position.clone(), P: Pw, Pi: Pw.clone().invert(),
        rotation: new THREE.Euler(), quaternion: new THREE.Quaternion(), position: new THREE.Vector3(),
        wpos: b.getWorldPosition(new THREE.Vector3()) };
    }
    // 손가락 굽히는 축: 손가락 방향 × 손바닥이 보는 쪽(몸 쪽). 엄지는 손바닥 가로질러(뒤쪽으로 조금 더)
    const axis = {};
    for (const [side, sg] of [['left', 1], ['right', -1]])
      for (const f of Object.keys(FINGERS)) {
        const parts = FINGERS[f], a = prox[`${side}${f}${parts[0]}`], b = prox[`${side}${f}${parts[1]}`];
        if (!a || !b) continue;
        const dir = b.wpos.clone().sub(a.wpos).normalize();
        const palm = new THREE.Vector3(-sg, 0, f === 'Thumb' ? -0.8 : 0).normalize();
        axis[`${side}${f}`] = dir.clone().cross(palm).normalize();
      }
    const dummy = { rotation: new THREE.Euler(), quaternion: new THREE.Quaternion(), position: new THREE.Vector3() };
    const meshes = []; root.traverse((o) => { if (o.isMesh && o.morphTargetDictionary) meshes.push(o); });
    const human = {
      scene: holder, scale: k, prox,
      humanoid: { getNormalizedBoneNode: (n) => prox[n] || dummy },
      expressionManager: { setValue(n, v) { const key = EXPR[n] || n; for (const m of meshes) { const i = m.morphTargetDictionary[key]; if (i !== undefined) m.morphTargetInfluences[i] = v; } } },
      legLength() { return prox.leftUpperLeg.wpos.y - prox.leftFoot.wpos.y; },
      // 손가락 굽히기: name = 'leftIndex' 등, amt = 각 마디 굽힘(라디안). 마디마다 [뿌리, 가운데, 끝] 비율로 나눠 줌
      curl(name, amt, spread = [1, 1.1, 0.8]) {
        const side = name.startsWith('left') ? 'left' : 'right', f = name.slice(side.length), ax = axis[name];
        if (!ax) return;
        FINGERS[f].forEach((p, i) => { const pr = prox[`${side}${f}${p}`]; if (pr) pr.quaternion.setFromAxisAngle(ax, amt * spread[i] * (f === 'Thumb' && i === 0 ? 0.5 : 1)); });
      },
      fist(side, amt) { for (const f of Object.keys(FINGERS)) this.curl(side + f, amt * (f === 'Thumb' ? 0.7 : 1)); },
      update() {
        for (const [n, p] of Object.entries(prox)) {
          const q = p.quaternion.clone().multiply(new THREE.Quaternion().setFromEuler(p.rotation));
          p.b.quaternion.copy(p.Pi).multiply(q).multiply(p.P).multiply(p.rest);
          if (n === 'hips') p.b.position.copy(p.restPos).add(p.position.clone().divideScalar(k).applyQuaternion(p.Pi));
        }
      },
    };
    ok(human);
  }, undefined, bad));
}
