import type { Interest, Profile, ProfileAttribute, SavedState } from './models';

export interface Recommendation {
  profile:Profile;
  sharedInterests:Interest[];
  sharedAttributes:ProfileAttribute[];
  sameGoal:boolean;
  score:number;
}

/** Normalize self-declared text, including Persian/Arabic spelling variants. */
export function normalized(value:string):string {
  return value.normalize('NFKC').replace(/ي/g,'ی').replace(/ك/g,'ک')
    .replace(/[\u200c\u200d]/g,' ').trim().replace(/\s+/g,' ').toLocaleLowerCase('fa');
}
export function attributeToken(attribute:ProfileAttribute):string {
  return normalized(attribute.key)+'='+normalized(attribute.value);
}
function tokens(profile:Profile):Map<string,number>{
  const values=new Map<string,number>(profile.interests.map(i=>['interest:'+i,1]));
  for(const attribute of profile.attributes)values.set('attribute:'+attributeToken(attribute),2);
  return values;
}
/** Weighted Dice similarity; only interests and explicitly supplied attributes are used. */
export function profileSimilarity(a:Profile,b:Profile):number {
  const left=tokens(a),right=tokens(b);
  let intersection=0,total=0;
  for(const [token,weight] of left){total+=weight;if(right.has(token))intersection+=weight;}
  for(const weight of right.values())total+=weight;
  return total?2*intersection/total:0;
}
export function recommend(profiles:Profile[],state:SavedState):Recommendation[]{
  const excluded=new Set([...state.likes,...state.passed,...state.avoided]);
  const references=profiles.filter(p=>state.avoided.includes(p.id));
  const mine=new Set(state.me.attributes.map(attributeToken));
  const interests=new Set(state.me.interests);
  const pref=state.preferences;
  return profiles.flatMap(profile=>{
    if(excluded.has(profile.id)||profile.age<pref.minAge||profile.age>pref.maxAge
      ||profile.distance>pref.distance||(pref.online&&!profile.online)
      ||(pref.interest!=='all'&&!profile.interests.includes(pref.interest as Interest)))return [];
    const similarity=references.reduce((max,reference)=>Math.max(max,profileSimilarity(profile,reference)),0);
    if(similarity>=0.6)return [];
    const sharedInterests=profile.interests.filter(i=>interests.has(i));
    const sharedAttributes=profile.attributes.filter(a=>mine.has(attributeToken(a)));
    const sameGoal=profile.relationshipGoal===state.me.relationshipGoal;
    const score=sharedInterests.length*2+sharedAttributes.length*3+(sameGoal?4:0)-similarity*8;
    return [{profile,sharedInterests,sharedAttributes,sameGoal,score}];
  }).sort((a,b)=>b.score-a.score||a.profile.distance-b.profile.distance||a.profile.id.localeCompare(b.profile.id));
}
