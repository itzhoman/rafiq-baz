import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { recommend, profileSimilarity, normalized } from '../src/app/recommendations.ts';
import type { Profile, SavedState } from '../src/app/models.ts';

const seed=JSON.parse(readFileSync(new URL('../shared/demo-data.json',import.meta.url),'utf8'));
const profiles=seed.profiles as Profile[];
const state=():SavedState=>structuredClone(seed.state);

test('like and pass advance the queue without changing other preferences',()=>{
  const s=state(),first=recommend(profiles,s)[0].profile.id;
  s.passed.push(first);
  assert(!recommend(profiles,s).some(r=>r.profile.id===first));
  s.passed=[];
  assert.equal(recommend(profiles,s)[0].profile.id,first);
  s.likes.push(first);
  assert(!recommend(profiles,s).some(r=>r.profile.id===first));
});
test('not like this hides a reference and very similar attributes, not distinct people',()=>{
  const reference=profiles.find(p=>p.id==='leila')!;
  const similar=profiles.find(p=>p.id==='sara')!;
  const distinct=profiles.find(p=>p.id==='armin')!;
  assert(profileSimilarity(reference,similar)>=0.6);
  assert(profileSimilarity(reference,distinct)<0.6);
  const s=state();s.avoided=['leila'];
  const ids=recommend(profiles,s).map(r=>r.profile.id);
  assert(!ids.includes('leila'));assert(!ids.includes('sara'));assert(ids.includes('armin'));
  s.avoided=[];assert(recommend(profiles,s).some(r=>r.profile.id==='sara'));
});
test('passing only one person does not hide a similar person',()=>{
  const s=state();s.passed=['leila'];
  assert(recommend(profiles,s).some(r=>r.profile.id==='sara'));
  assert.deepEqual(s.avoided,[]);
});
test('self-declared attributes and relationship intention personalize order',()=>{
  const s=state();
  s.me.interests=[];
  s.me.relationshipGoal='exploring';
  s.me.attributes=[{key:'سبک زندگی',value:'ماجراجو'},{key:'ارتباط',value:'مستقل'}];
  assert.equal(recommend(profiles,s)[0].profile.id,'nika');
  s.me.relationshipGoal='long_term';
  s.me.attributes=[{key:'سبک زندگی',value:'آرام'},{key:'ارتباط',value:'گفتگو محور'}];
  assert.notEqual(recommend(profiles,s)[0].profile.id,'nika');
});
test('filters remain hard constraints after ranking',()=>{
  const s=state();s.preferences.distance=5;s.preferences.online=true;
  assert(recommend(profiles,s).every(r=>r.profile.distance<=5&&r.profile.online));
  s.preferences.minAge=79;s.preferences.maxAge=80;
  assert.deepEqual(recommend(profiles,s),[]);
});
test('text normalization aligns Arabic and Persian variants without inferring other traits',()=>{
  assert.equal(normalized('  سبك   زندگي '),normalized('سبک زندگی'));
  const a=structuredClone(profiles[0]),b=structuredClone(a);
  b.name='Other';b.age=40;b.city='Other';b.image='/unrelated.webp';b.relationshipGoal='exploring';
  assert.equal(profileSimilarity(a,b),1);
});
