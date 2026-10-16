export type Page = 'discover' | 'find' | 'likes' | 'connections' | 'messages' | 'profile';
export type RelationshipGoal = 'long_term' | 'intentional' | 'exploring';
export interface ProfileAttribute { key:string; value:string }
export type Interest = 'coffee' | 'music' | 'travel' | 'photo' | 'art' | 'hiking' | 'books' | 'cinema';
export interface Profile {
  id: string; name: string; nameFa: string; age: number; city: string; cityFa: string;
  distance: number; image: string; online: boolean; verified: boolean; likesYou: boolean;
  bio: string; bioFa: string; prompt: string; promptFa: string; interests: Interest[];
  relationshipGoal: RelationshipGoal; attributes: ProfileAttribute[];
}
export interface Message { id: string; text: string; mine: boolean; time: string }
export interface Preferences { minAge: number; maxAge: number; distance: number; interest: string; online: boolean }
export interface Me { name: string; age: number; city: string; bio: string; interests: Interest[]; relationshipGoal:RelationshipGoal; attributes:ProfileAttribute[] }
export interface SavedState {
  likes: string[]; passed: string[]; saved: string[]; connections: string[];
  avoided: string[];
  messages: Record<string, Message[]>; preferences: Preferences; me: Me;
}
export const RELATIONSHIP_GOALS:Record<RelationshipGoal,{fa:string;en:string}>={
  long_term:{fa:'رابطهٔ جدی و بلندمدت',en:'A long-term relationship'},
  intentional:{fa:'آشنایی با هدف رابطه',en:'Intentional dating'},
  exploring:{fa:'شناختن و تصمیم گرفتن',en:'Exploring a connection'}
};
export const INTERESTS: Record<Interest, {fa:string; en:string; icon:string}> = {
  coffee:{fa:'قهوه',en:'Coffee',icon:'coffee'}, music:{fa:'موسیقی',en:'Music',icon:'music'},
  travel:{fa:'سفر',en:'Travel',icon:'compass'}, photo:{fa:'عکاسی',en:'Photography',icon:'camera'},
  art:{fa:'هنر',en:'Art',icon:'spark'}, hiking:{fa:'طبیعت‌گردی',en:'Hiking',icon:'mountain'},
  books:{fa:'کتاب',en:'Books',icon:'book'}, cinema:{fa:'سینما',en:'Cinema',icon:'play'}
};
