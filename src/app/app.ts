import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, ViewChild, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { IconComponent } from './icon';
import { AppStore } from './store';
import { INTERESTS, RELATIONSHIP_GOALS, Interest, Me, Page, Preferences, Profile, RelationshipGoal } from './models';
import { FinderComponent } from './finder';
import { normalized } from './recommendations';
import { AuthStore } from './auth.store';
import { AuthComponent } from './auth';

type Modal = 'filters'|'notifications'|'settings'|'match'|'detail'|'auth'|null;
@Component({
  selector:'rb-app', standalone:true, imports:[IconComponent,FormsModule,FinderComponent,AuthComponent],
  changeDetection:ChangeDetectionStrategy.OnPush,
  templateUrl:'./app.html'
})
export class AppComponent {
  readonly store=inject(AppStore);
  readonly auth=inject(AuthStore);
  private readonly changeDetector=inject(ChangeDetectorRef);
  @ViewChild('dialog') dialog!:ElementRef<HTMLDialogElement>;
  readonly lang=signal<'fa'|'en'>('fa');
  readonly page=signal<Page>(this.initialPage());
  readonly tab=signal<'forYou'|'nearby'|'online'>('forYou');
  readonly likesTab=signal<'liked'|'saved'>('liked');
  readonly selectedId=signal('leila');
  readonly chatId=signal('armin');
  readonly modal=signal<Modal>(null);
  readonly matchProfile=signal<Profile|null>(null);
  readonly detailProfile=signal<Profile|null>(null);
  readonly toast=signal('');
  readonly lastPassed=signal<string|null>(null);
  readonly mobilePreview=location.pathname==='/mobile';
  readonly interests=INTERESTS;
  readonly goals=RELATIONSHIP_GOALS;
  readonly goalKeys=Object.keys(RELATIONSHIP_GOALS) as RelationshipGoal[];
  readonly interestKeys=Object.keys(INTERESTS) as Interest[];
  readonly visible=computed(()=>{
    const profiles=this.store.discovery();
    if(this.tab()==='nearby')return [...profiles].sort((a,b)=>a.distance-b.distance);
    if(this.tab()==='online')return profiles.filter(p=>p.online);
    return profiles;
  });
  readonly active=computed<Profile|null>(()=>this.visible().find(p=>p.id===this.selectedId())||this.visible()[0]||null);
  readonly upcoming=computed(()=>this.visible().filter(p=>p.id!==this.active()?.id).slice(0,4));
  readonly chat=computed<Profile|null>(()=>this.store.connections().find(p=>p.id===this.chatId())||this.store.connections()[0]||null);
  readonly messages=computed(()=>this.store.state().messages[this.chat()?.id||'']||[]);
  readonly filteredCount=computed(()=>{
    const p=this.store.state().preferences;let count=0;
    if(p.minAge!==25||p.maxAge!==35)count++;
    if(p.distance!==50)count++;if(p.interest!=='all')count++;if(p.online)count++;
    return count;
  });
  readonly list=computed(()=>this.likesTab()==='saved'?this.store.saved():this.store.liked());
  readonly navs:{page:Page;icon:string;fa:string;en:string}[]=[
    {page:'find',icon:'flame',fa:'پیدا کردن',en:'Find someone'},
    {page:'discover',icon:'grid',fa:'کشف آدم‌ها',en:'Discover'},
    {page:'likes',icon:'heart',fa:'پسندیده‌ها',en:'Likes'},
    {page:'connections',icon:'users',fa:'ارتباط‌ها',en:'Connections'},
    {page:'messages',icon:'chat',fa:'پیام‌ها',en:'Messages'},
    {page:'profile',icon:'user',fa:'پروفایل من',en:'My profile'}
  ];
  draftPrefs:Preferences={...this.store.state().preferences};
  draftMe:Me=structuredClone(this.store.state().me);
  attributeKey='';attributeValue='';
  messageText='';searchText='';
  readonly chatSearch=signal('');
  readonly chatList=computed(()=>this.store.connections().filter(p=>(p.name+' '+p.nameFa).toLowerCase().includes(this.chatSearch().toLowerCase())));
  private toastTimer:ReturnType<typeof setTimeout>|undefined;
  constructor(){
    document.documentElement.lang='fa';
    document.documentElement.dir='rtl';
    void this.store.ready.then(()=>{this.draftMe=structuredClone(this.store.state().me);this.changeDetector.markForCheck();});
  }
  txt(fa:string,en:string):string{return this.lang()==='fa'?fa:en;}
  name(p:Profile):string{return this.lang()==='fa'?p.nameFa:p.name;}
  city(p:Profile):string{return this.lang()==='fa'?p.cityFa:p.city;}
  bio(p:Profile):string{return this.lang()==='fa'?p.bioFa:p.bio;}
  label(interest:Interest):string{return this.lang()==='fa'?INTERESTS[interest].fa:INTERESTS[interest].en;}
  shared(p:Profile):Interest[]{return p.interests.filter(i=>this.store.state().me.interests.includes(i));}
  title():string{
    const nav=this.navs.find(n=>n.page===this.page())!;
    return this.txt(nav.fa,nav.en);
  }
  switchLang():void{
    this.lang.update(v=>v==='fa'?'en':'fa');
    document.documentElement.lang=this.lang();document.documentElement.dir=this.lang()==='fa'?'rtl':'ltr';
  }
  private initialPage():Page{
    const page=new URLSearchParams(location.search).get('view') as Page;
    return ['find','discover','likes','connections','messages','profile'].includes(page)?page:'find';
  }
  navigate(page:Page):void{
    if(page==='profile'&&this.page()!=='profile'){
      this.draftMe=structuredClone(this.store.state().me);this.attributeKey='';this.attributeValue='';
    }
    this.page.set(page);
    const url=new URL(location.href);url.searchParams.set('view',page);
    history.replaceState(null,'',url);
    window.scrollTo({top:0,behavior:'instant'});
  }
  openModal(modal:Modal):void{
    if(modal==='filters')this.draftPrefs={...this.store.state().preferences};
    this.modal.set(modal);
    if(!this.dialog.nativeElement.open)this.dialog.nativeElement.showModal();
  }
  closeModal():void{this.dialog.nativeElement.close();this.modal.set(null);}
  async accountReady():Promise<void>{
    this.closeModal();this.store.clearAccountView();await this.store.load();
    this.draftMe=structuredClone(this.store.state().me);this.navigate('profile');
    this.notify(this.txt('حسابت آماده است؛ پروفایلت را کامل کن.','Your account is ready. Make your profile yours.'));
  }
  async logout():Promise<void>{
    if(await this.auth.logout()){
      this.store.clearAccountView();await this.store.load();this.closeModal();this.navigate('find');
      this.notify(this.txt('از حساب خارج شدی.','You have signed out.'));
    }
  }
  backdrop(event:MouseEvent):void{if(event.target===this.dialog.nativeElement)this.closeModal();}
  notify(message:string,allowUndo=false):void{
    if(!allowUndo)this.lastPassed.set(null);
    if(this.toastTimer)clearTimeout(this.toastTimer);
    this.toast.set(message);this.toastTimer=setTimeout(()=>this.toast.set(''),4000);
  }
  async like(profile:Profile):Promise<void>{
    const isMatch=await this.store.action(profile.id,'like');
    if(this.store.error())return;
    if(this.page()==='find')window.scrollTo({top:0,behavior:'instant'});
    if(isMatch){this.matchProfile.set(profile);this.openModal('match');}
    else this.notify(this.txt('به پسندیده‌ها اضافه شد','Added to your likes'));
  }
  async pass(profile:Profile):Promise<void>{
    await this.store.action(profile.id,'pass');
    if(!this.store.error()){
      if(this.page()==='find')window.scrollTo({top:0,behavior:'instant'});
      this.lastPassed.set(profile.id);this.notify(this.txt('پروفایل بعدی؛ شاید همین یکی!','On to the next connection'),true);
    }
  }
  async avoid(profile:Profile):Promise<void>{
    if(this.store.busy())return;
    this.lastPassed.set(null);
    await this.store.action(profile.id,'avoid');
    if(this.page()==='find'&&!this.store.error())window.scrollTo({top:0,behavior:'instant'});
    if(!this.store.error())this.notify(this.txt('این فرد و الگوهای بسیار مشابه از پیشنهادها کنار گذاشته شدند.','This person and very similar profiles are now hidden.'));
  }
  async undo():Promise<void>{
    const id=this.lastPassed();if(!id)return;
    await this.store.action(id,'undo');this.selectedId.set(id);this.lastPassed.set(null);this.toast.set('');
  }
  async save(profile:Profile):Promise<void>{
    await this.store.action(profile.id,'save');
    if(!this.store.error())this.notify(this.store.state().saved.includes(profile.id)
      ?this.txt('برای بعد ذخیره شد','Saved for later'):this.txt('از ذخیره‌ها برداشته شد','Removed from saved'));
  }
  async applyFilters():Promise<void>{
    if(this.draftPrefs.minAge>this.draftPrefs.maxAge){this.notify(this.txt('بازهٔ سن را درست انتخاب کن','Minimum age must be below maximum age'));return;}
    await this.store.preferences({...this.draftPrefs});this.closeModal();
  }
  resetDraft():void{this.draftPrefs={minAge:25,maxAge:35,distance:50,interest:'all',online:false};}
  async clearFilters():Promise<void>{this.tab.set('forYou');await this.store.preferences({minAge:18,maxAge:80,distance:200,interest:'all',online:false});}
  detail(profile:Profile):void{this.detailProfile.set(profile);this.openModal('detail');}
  startChat(profile:Profile):void{
    this.chatId.set(profile.id);this.navigate('messages');this.closeModal();
  }
  async send():Promise<void>{
    const profile=this.chat(),text=this.messageText.trim();
    if(!profile||!text)return;
    if(await this.store.send(profile.id,text)){
      this.messageText='';
      requestAnimationFrame(()=>document.getElementById('chat-end')?.scrollIntoView({behavior:'smooth',block:'nearest'}));
    }
  }
  selectInterest(interest:Interest):void{
    this.draftMe={...this.draftMe,interests:this.draftMe.interests.includes(interest)
      ?this.draftMe.interests.filter(i=>i!==interest):[...this.draftMe.interests,interest]};
  }
  addAttribute():boolean{
    const key=this.attributeKey.trim(),value=this.attributeValue.trim();
    if(!key||!value||key.length>32||value.length>80){
      this.notify(this.txt('برای ویژگی، عنوان و مقدار معتبر وارد کن.','Enter a valid attribute name and value.'));return false;
    }
    if(this.draftMe.attributes.length>=12){
      this.notify(this.txt('حداکثر ۱۲ ویژگی می‌توانی ثبت کنی.','You can add up to 12 attributes.'));return false;
    }
    if(this.draftMe.attributes.some(a=>normalized(a.key)===normalized(key))){
      this.notify(this.txt('این عنوان قبلاً ثبت شده؛ ابتدا ویژگی قبلی را حذف کن.','This attribute already exists. Remove it before replacing it.'));return false;
    }
    this.draftMe={...this.draftMe,attributes:[...this.draftMe.attributes,{key,value}]};
    this.attributeKey='';this.attributeValue='';return true;
  }
  removeAttribute(index:number):void{
    this.draftMe={...this.draftMe,attributes:this.draftMe.attributes.filter((_,i)=>i!==index)};
  }
  async saveProfile():Promise<void>{
    if(!this.draftMe.name.trim()||!this.draftMe.city.trim()||!Number.isInteger(this.draftMe.age)||this.draftMe.age<18||this.draftMe.age>80){
      this.notify(this.txt('نام، شهر و سن معتبر (۱۸ تا ۸۰) را وارد کن','Enter a name, city and valid age (18–80)'));return;
    }
    if((this.attributeKey.trim()||this.attributeValue.trim())&&!this.addAttribute())return;
    if(await this.store.saveMe({...this.draftMe,name:this.draftMe.name.trim(),city:this.draftMe.city.trim(),attributes:this.draftMe.attributes.map(a=>({...a}))}))
      this.notify(this.txt('پروفایل ذخیره شد؛ پیشنهادها بر اساس ویژگی‌هایت به‌روز شدند.','Profile saved. Your suggestions have been updated.'));
  }
  lastMessage(id:string):string{return this.store.state().messages[id]?.at(-1)?.text||this.txt('گفتگو را شروع کن','Start a conversation');}
  previewMobile():void{location.href=(this.mobilePreview?'/':'/mobile')+'?view='+this.page();}
}
