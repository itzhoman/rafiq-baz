import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import type { Profile } from '../src/app/models.ts';

const profiles=JSON.parse(readFileSync(new URL('../public/data/profiles.json',import.meta.url),'utf8')) as Profile[];
test('the fixture contains 100 additional complete adult profiles with local avatars',()=>{
  assert.equal(profiles.length,110);
  assert.equal(new Set(profiles.map(p=>p.id)).size,110);
  const added=profiles.filter(p=>p.id.startsWith('demo-'));
  assert.equal(added.length,100);
  for(const p of added){
    for(const field of ['name','nameFa','city','cityFa','bio','bioFa','prompt','promptFa'] as const)assert(p[field].trim().length>0,`${p.id}: ${field}`);
    assert(p.age>=18&&p.age<=80);
    assert(p.distance>0&&p.distance<=200);
    assert(p.interests.length>=4);
    assert(p.attributes.length>=8);
    assert.equal(new Set(p.attributes.map(a=>a.key)).size,p.attributes.length);
    assert(p.attributes.every(a=>a.key.trim()&&a.value.trim()));
    assert(['long_term','intentional','exploring'].includes(p.relationshipGoal));
    assert(p.image.startsWith('/assets/people/'));
    assert(existsSync(new URL('../public'+p.image,import.meta.url)));
    assert.equal(p.verified,false);
  }
});
