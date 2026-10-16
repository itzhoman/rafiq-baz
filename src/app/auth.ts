import { ChangeDetectionStrategy, Component, ElementRef, OnDestroy, ViewChild, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthStore, Signup } from './auth.store';
import { IconComponent } from './icon';

interface GoogleIdentity {
  initialize(options:{client_id:string;nonce:string;callback:(result:{credential:string})=>void;auto_select:boolean}):void;
  renderButton(target:HTMLElement,options:Record<string,string|number>):void;
  disableAutoSelect():void;
}
declare global {interface Window { google?:{accounts:{id:GoogleIdentity}} }}
let googleScript:Promise<void>|undefined;

@Component({
  selector:'rb-auth',standalone:true,imports:[FormsModule,IconComponent],
  templateUrl:'./auth.html',styleUrl:'./auth.css',changeDetection:ChangeDetectionStrategy.OnPush
})
export class AuthComponent implements OnDestroy {
  readonly auth=inject(AuthStore);
  readonly lang=input<'fa'|'en'>('fa');
  readonly authenticated=output<void>();
  readonly mode=signal<'login'|'signup'>('signup');
  readonly showPassword=signal(false);
  readonly googleReady=signal(false);
  readonly googleBusy=signal(false);
  @ViewChild('googleButton') googleButton?:ElementRef<HTMLElement>;
  form:Signup={name:'',email:'',password:'',age:25,city:''};
  adult=false;
  private destroyed=false;
  txt(fa:string,en:string):string{return this.lang()==='fa'?fa:en;}
  togglePassword():void{this.showPassword.update(value=>!value);}
  switchMode():void{this.mode.update(value=>value==='login'?'signup':'login');this.auth.error.set('');this.form.password='';}
  async submit():Promise<void>{
    if(this.mode()==='signup'&&!this.adult){this.auth.error.set('برای ساخت حساب باید حداقل ۱۸ سال داشته باشی.');return;}
    const body=this.mode()==='signup'?{...this.form,email:this.form.email.trim(),name:this.form.name.trim(),city:this.form.city.trim()}:{email:this.form.email.trim(),password:this.form.password};
    if(await this.auth.authenticate(this.mode()==='signup'?'/register':'/login',body)){
      this.form.password='';this.authenticated.emit();
    }
  }
  async prepareGoogle():Promise<void>{
    if(!this.adult||!Number.isInteger(this.form.age)||this.form.age<18||this.form.age>80||!this.form.city.trim()){
      this.auth.error.set('برای اولین ورود گوگل، سن و شهر را کامل کن و داشتن حداقل ۱۸ سال را تأیید کن.');return;
    }
    if(!this.auth.googleClientId()||this.googleBusy())return;
    this.googleBusy.set(true);this.auth.error.set('');
    try{
      const nonce=await this.auth.challenge();
      googleScript??=new Promise<void>((resolve,reject)=>{
        if(window.google?.accounts.id){resolve();return;}
        const script=document.createElement('script');script.src='https://accounts.google.com/gsi/client';script.async=true;
        script.onload=()=>resolve();script.onerror=()=>{script.remove();googleScript=undefined;reject(new Error('Google script unavailable'));};document.head.append(script);
      });
      await googleScript;
      if(this.destroyed)return;
      const google=window.google?.accounts.id;
      if(!google||!this.googleButton)throw new Error('Google unavailable');
      google.initialize({client_id:this.auth.googleClientId(),nonce,auto_select:false,callback:result=>void this.finishGoogle(result.credential)});
      google.renderButton(this.googleButton.nativeElement,{theme:'outline',size:'large',type:'standard',text:'continue_with',shape:'pill',width:300,locale:this.lang()});
      this.googleReady.set(true);
    }catch{this.auth.error.set('بارگذاری ورود گوگل انجام نشد. دوباره تلاش کن.');}
    finally{this.googleBusy.set(false);}
  }
  private async finishGoogle(credential:string):Promise<void>{
    if(this.destroyed)return;
    if(await this.auth.authenticate('/google',{credential,age:this.form.age,city:this.form.city}))this.authenticated.emit();
  }
  ngOnDestroy():void{this.destroyed=true;this.form.password='';}
}
