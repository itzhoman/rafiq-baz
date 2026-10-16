import { Injectable, computed, signal } from '@angular/core';
import { Me, Preferences, Profile, SavedState } from './models';
import { initialState } from './seed';
import { recommend } from './recommendations';

type RuntimeConfig = { mode:'demo'|'api'; apiBase:string };
declare global { interface Window { __RB_CONFIG__?: RuntimeConfig } }
const KEY='rafiq-baz.v1';
class SessionChanged extends Error {}

@Injectable({providedIn:'root'})
export class AppStore {
  readonly profiles=signal<Profile[]>([]);
  readonly profilesLoading=signal(true);
  readonly apiMode=window.__RB_CONFIG__?.mode==='api';
  readonly state=signal<SavedState>(this.apiMode?initialState():this.restore());
  readonly busy=signal(false);
  readonly error=signal('');
  private readonly apiBase=window.__RB_CONFIG__?.apiBase||'';
  private readonly session=this.getSession();
  private revision=0;
  readonly liked=computed(()=>this.profiles().filter(p=>this.state().likes.includes(p.id)));
  readonly connections=computed(()=>this.profiles().filter(p=>this.state().connections.includes(p.id)));
  readonly saved=computed(()=>this.profiles().filter(p=>this.state().saved.includes(p.id)));
  readonly recommendations=computed(()=>recommend(this.profiles(),this.state()));
  readonly discovery=computed(()=>this.recommendations().map(item=>item.profile));
  readonly ready:Promise<void>;
  constructor(){this.ready=this.apiMode?this.load():this.loadDemoProfiles();}
  private async loadDemoProfiles():Promise<void>{
    try{
      const response=await fetch('/data/profiles.json',{signal:AbortSignal.timeout(10000)});
      if(!response.ok)throw new Error('Profiles unavailable');
      this.profiles.set(await response.json() as Profile[]);
    }catch{this.error.set('بارگذاری همهٔ پروفایل‌های نمونه انجام نشد. صفحه را دوباره باز کن.');}
    finally{this.profilesLoading.set(false);}
  }

  private restore():SavedState {
    const fresh=initialState();
    try{
      const raw=localStorage.getItem(KEY);
      if(!raw)return fresh;
      const parsed=JSON.parse(raw);
      if(!parsed||!['likes','passed','saved','connections'].every(k=>Array.isArray(parsed[k])
        &&parsed[k].every((id:unknown)=>typeof id==='string')))return fresh;
      const me={...fresh.me,...parsed.me};
      if(!Array.isArray(me.attributes)||!me.attributes.every((a:unknown)=>!!a&&typeof a==='object'
        &&'key' in a&&'value' in a&&typeof a.key==='string'&&typeof a.value==='string'))me.attributes=[];
      if(!['long_term','intentional','exploring'].includes(me.relationshipGoal))me.relationshipGoal=fresh.me.relationshipGoal;
      if(me.bio==='دنبال رفاقت‌های خوب و تجربه‌های تازه. قهوه، موسیقی و سفر همیشه توی برنامه‌مه.')me.bio=fresh.me.bio;
      const avoided=Array.isArray(parsed.avoided)?parsed.avoided.filter((id:unknown)=>typeof id==='string'):[];
      return {...fresh,...parsed,avoided,preferences:{...fresh.preferences,...parsed.preferences},me};
    }catch{return fresh;}
  }
  private getSession():string {
    try{
      const value=localStorage.getItem(KEY+'.session');
      if(value&&/^[0-9a-f-]{36}$/i.test(value))return value;
      const id=crypto.randomUUID();localStorage.setItem(KEY+'.session',id);return id;
    }catch{return crypto.randomUUID();}
  }
  private persist(next:SavedState):void {
    this.state.set(next);
    if(this.apiMode)return;
    try{localStorage.setItem(KEY,JSON.stringify(next));}catch{this.error.set('فضای ذخیره‌سازی مرورگر در دسترس نیست.');}
  }
  private async request<T>(path:string,body?:unknown):Promise<T>{
    const revision=this.revision;
    try{
    const response=await fetch(this.apiBase+'/api/v1'+path,{
      method:body===undefined?'GET':'POST',credentials:'include',
      headers:{'Content-Type':'application/json','X-Demo-Session':this.session,'X-RB-Client':'web'},
      ...(body===undefined?{}:{body:JSON.stringify(body)}),
      signal:AbortSignal.timeout(10000)
    });
    if(!response.ok)throw new Error('درخواست انجام نشد. دوباره تلاش کن.');
    const result=await response.json() as T;
    if(revision!==this.revision)throw new SessionChanged();
    return result;
    }catch(error){if(revision!==this.revision)throw new SessionChanged();throw error;}
  }
  async load():Promise<void>{
    this.busy.set(true);
    try{
      const [profiles,state]=await Promise.all([this.request<Profile[]>('/profiles'),this.request<SavedState>('/state')]);
      this.profiles.set(profiles);this.persist(state);this.error.set('');
    }catch(error){if(error instanceof SessionChanged)return;this.error.set('ارتباط با سرور برقرار نشد. اتصال را بررسی و دوباره تلاش کن.');}
    finally{this.busy.set(false);this.profilesLoading.set(false);}
  }
  clearAccountView():void{this.revision++;this.state.set(initialState());this.error.set('');}
  async action(id:string,kind:'like'|'pass'|'save'|'undo'|'avoid'|'undo_avoid'):Promise<boolean>{
    if(this.busy())return false;
    const profile=this.profiles().find(p=>p.id===id);if(!profile)return false;
    this.error.set('');
    const before=this.state();
    let next:SavedState={...before};
    if(kind==='like'){
      next.likes=[...new Set([...before.likes,id])];
      if(profile.likesYou)next.connections=[...new Set([...before.connections,id])];
    }
    if(kind==='pass')next.passed=[...new Set([...before.passed,id])];
    if(kind==='undo')next.passed=before.passed.filter(v=>v!==id);
    if(kind==='avoid')next.avoided=[...new Set([...before.avoided,id])];
    if(kind==='undo_avoid')next.avoided=before.avoided.filter(v=>v!==id);
    if(kind==='save')next.saved=before.saved.includes(id)?before.saved.filter(v=>v!==id):[...before.saved,id];
    this.persist(next);
    if(this.apiMode){
      this.busy.set(true);
      try{next=await this.request<SavedState>('/actions',{profile_id:id,kind});this.persist(next);this.error.set('');}
      catch(error){if(error instanceof SessionChanged)return false;this.persist(before);this.error.set('تغییر ذخیره نشد؛ دوباره تلاش کن.');return false;}
      finally{this.busy.set(false);}
    }
    return kind==='like'&&!before.connections.includes(id)&&next.connections.includes(id);
  }
  async preferences(preferences:Preferences):Promise<void>{
    const before=this.state();this.persist({...before,preferences});
    if(this.apiMode){
      try{this.persist(await this.request<SavedState>('/preferences',preferences));}
      catch(error){if(error instanceof SessionChanged)return;this.persist(before);this.error.set('فیلترها ذخیره نشدند.');}
    }
  }
  async saveMe(me:Me):Promise<boolean>{
    if(this.busy())return false;
    this.error.set('');
    const before=this.state();this.persist({...before,me});
    if(this.apiMode){
      this.busy.set(true);
      try{this.persist(await this.request<SavedState>('/me',me));}
      catch(error){if(error instanceof SessionChanged)return false;this.persist(before);this.error.set('پروفایل ذخیره نشد.');return false;}
      finally{this.busy.set(false);}
    }return true;
  }
  async send(id:string,text:string):Promise<boolean>{
    text=text.trim();
    if(!text||text.length>1000||!this.state().connections.includes(id))return false;
    if(this.apiMode){
      try{
        this.persist(await this.request<SavedState>('/messages',{profile_id:id,text}));
        this.error.set('');return true;
      }catch(error){if(error instanceof SessionChanged)return false;this.error.set('پیام ذخیره نشد. دوباره تلاش کن.');return false;}
    }
    const before=this.state();
    const message={id:crypto.randomUUID(),text,mine:true,time:new Intl.DateTimeFormat('fa',{hour:'2-digit',minute:'2-digit'}).format(new Date())};
    this.persist({...before,messages:{...before.messages,[id]:[...(before.messages[id]||[]),message]}});
    return true;
  }
  async resetPasses():Promise<void>{
    const before=this.state();
    if(this.apiMode){
      try{this.persist(await this.request<SavedState>('/reset-passes',{}));}
      catch(error){if(error instanceof SessionChanged)return;this.error.set('بازیابی پروفایل‌ها انجام نشد.');}
    }else this.persist({...before,passed:[]});
  }
}
