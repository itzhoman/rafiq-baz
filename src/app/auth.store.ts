import { Injectable, signal } from '@angular/core';

export interface AccountUser { id:string; name:string; email:string; provider:'email'|'google' }
export interface Signup { name:string; email:string; password:string; age:number; city:string }

@Injectable({providedIn:'root'})
export class AuthStore {
  readonly user=signal<AccountUser|null>(null);
  readonly busy=signal(false);
  readonly error=signal('');
  readonly emailEnabled=signal(false);
  readonly googleClientId=signal('');
  readonly apiMode=window.__RB_CONFIG__?.mode==='api';
  private readonly base=window.__RB_CONFIG__?.apiBase||'';
  readonly ready=this.refresh();

  private async request<T>(path:string,body?:unknown):Promise<T>{
    const response=await fetch(this.base+'/api/v1/auth'+path,{
      method:body===undefined?'GET':'POST',credentials:'include',
      headers:{'Content-Type':'application/json','X-RB-Client':'web'},
      ...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(15000)
    });
    const result=await response.json();
    if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'اطلاعات واردشده معتبر نیست. دوباره بررسی کن.');
    return result as T;
  }
  async refresh():Promise<void>{
    if(!this.apiMode)return;
    try{
      const result=await this.request<{user:AccountUser|null;googleClientId:string;emailEnabled:boolean}>('/status');
      this.user.set(result.user);this.googleClientId.set(result.googleClientId);this.emailEnabled.set(result.emailEnabled);
    }catch{this.error.set('سرویس حساب‌ها در دسترس نیست. دوباره تلاش کن.');}
  }
  async authenticate(path:'/register'|'/login'|'/google',body:unknown):Promise<boolean>{
    if(this.busy()||!this.emailEnabled())return false;
    this.busy.set(true);this.error.set('');
    try{const result=await this.request<{user:AccountUser}>(path,body);this.user.set(result.user);return true;}
    catch(error){this.error.set(error instanceof Error?error.message:'ورود انجام نشد.');return false;}
    finally{this.busy.set(false);}
  }
  async challenge():Promise<string>{return (await this.request<{nonce:string}>('/google/challenge',{})).nonce;}
  async logout():Promise<boolean>{
    if(this.busy())return false;
    this.busy.set(true);this.error.set('');
    try{await this.request('/logout',{});this.user.set(null);return true;}
    catch{this.error.set('خروج انجام نشد؛ دوباره تلاش کن.');return false;}
    finally{this.busy.set(false);}
  }
}
