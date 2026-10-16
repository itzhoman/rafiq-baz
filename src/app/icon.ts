import { ChangeDetectionStrategy, Component, input } from '@angular/core';
const PATHS:Record<string,string[]>={
 heart:['M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z'],
 flame:['M12 3c1 4-4 5-4 9 0 2 1 3 2 3-1-4 3-5 3-8 5 4 7 7 5 11-3 5-11 4-12-1C4 11 9 7 12 3Z'],
 compass:['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z','m16 8-3 5-5 3 3-5 5-3Z'],
 users:['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2','M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z','M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8'],
 chat:['M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z'],
 user:['M20 21v-2a7 7 0 0 0-14 0v2','M13 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z'],
 settings:['M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z','m9 3 .7-1h4.6l.7 1 .4 2 2 1 2-.6 1.5 1.5-.6 2 1 2 2 .4 1 .7v3l-1 .7-2 .4-1 2 .6 2-1.5 1.5-2-.6-2 1-.4 2h-5l-.4-2-2-1-2 .6L2.6 19l.6-2-1-2-1-.4v-5l1-.4 1-2-.6-2L4 3.7l2 .6 2-1Z'],
 sliders:['M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3','M1 14h6M9 8h6M17 16h6'],
 bell:['M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4'],
 search:['M21 21l-4.3-4.3','M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z'],
 arrow:['M19 12H5m7-7-7 7 7 7'],
 chevron:['m15 18-6-6 6-6'],
 close:['m6 6 12 12M6 18 18 6'],
 check:['m5 12 4 4L19 6'],
 shield:['m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6l8-4Z','m8 12 3 3 5-6'],
 pin:['M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z','M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
 coffee:['M3 3h15v10a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5V3ZM18 5h2a3 3 0 1 1 0 6h-2M1 22h20'],
 music:['M9 18V5l12-2v13','M9 18a3 3 0 1 1-3-3h3M21 16a3 3 0 1 1-3-3h3'],
 camera:['M14 4h-4L8 7H3a1 1 0 0 0-1 1v12h20V8a1 1 0 0 0-1-1h-5l-2-3Z','M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z'],
 mountain:['m2 20 7-15 5 10 3-7 5 12H2ZM6 12l3 2 3-2'],
 spark:['m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7Z'],
 book:['M12 5C8 2 4 3 2 4v16c4-2 7-1 10 1 3-2 6-3 10-1V4c-2-1-6-2-10 1Zm0 0v16'],
 play:['m9 5 11 7-11 7V5Z'],
 bookmark:['M5 3h14v19l-7-5-7 5V3Z'],
 undo:['M3 10h12a6 6 0 0 1 0 12','m3 10 6-6m-6 6 6 6'],
 globe:['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM2 12h20','M12 2a20 20 0 0 0 0 20 20 20 0 0 0 0-20Z'],
 phone:['M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2ZM10 18h4M10 5h4'],
 send:['m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13'],
 edit:['m16 3 5 5-13 13-6 1 1-6L16 3Z'],
 grid:['M3 3h7v7H3V3ZM14 3h7v7h-7V3ZM3 14h7v7H3v-7ZM14 14h7v7h-7v-7Z'],
 info:['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM12 11v6M12 7h.01'],
 sun:['M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1 1M18 18l1 1M5 19l1-1M18 6l1-1']
};
@Component({
 selector:'rb-icon',standalone:true,changeDetection:ChangeDetectionStrategy.OnPush,
 template:'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" [attr.fill]="filled() ? \'currentColor\' : \'none\'" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">@for(path of paths[name()] || paths[\'spark\']; track path){<path [attr.d]="path"/>}</svg>',
 styles:[':host{display:inline-flex;inline-size:22px;block-size:22px;flex-shrink:0;align-items:center;justify-content:center}svg{width:100%;height:100%}']
})
export class IconComponent {
 readonly name=input('spark');readonly filled=input(false);readonly paths=PATHS;
}
