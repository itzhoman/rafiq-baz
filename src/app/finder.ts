import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';
import { AppStore } from './store';
import { IconComponent } from './icon';
import { INTERESTS, RELATIONSHIP_GOALS, Profile, ProfileAttribute, RelationshipGoal } from './models';
import { attributeToken, Recommendation } from './recommendations';

@Component({
  selector:'rb-finder',standalone:true,imports:[IconComponent],
  changeDetection:ChangeDetectionStrategy.OnPush,
  templateUrl:'./finder.html',styleUrl:'./finder.css'
})
export class FinderComponent {
  readonly store=inject(AppStore);
  readonly lang=input<'fa'|'en'>('fa');
  readonly likeProfile=output<Profile>();
  readonly passProfile=output<Profile>();
  readonly avoidProfile=output<Profile>();
  readonly editProfile=output<void>();
  readonly openFilters=output<void>();
  readonly current=computed(()=>this.store.recommendations().slice(0,1));
  readonly avoidedProfiles=computed(()=>this.store.profiles().filter(p=>this.store.state().avoided.includes(p.id)));
  readonly interests=INTERESTS;
  txt(fa:string,en:string):string{return this.lang()==='fa'?fa:en;}
  name(profile:Profile):string{return this.txt(profile.nameFa,profile.name);}
  goal(goal:RelationshipGoal):string{return this.txt(RELATIONSHIP_GOALS[goal].fa,RELATIONSHIP_GOALS[goal].en);}
  isShared(suggestion:Recommendation,attribute:ProfileAttribute):boolean{
    return suggestion.sharedAttributes.some(value=>attributeToken(value)===attributeToken(attribute));
  }
  async restorePattern(profile:Profile):Promise<void>{await this.store.action(profile.id,'undo_avoid');}
}
