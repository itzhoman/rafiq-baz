import { bootstrapApplication } from '@angular/platform-browser';
import { provideZonelessChangeDetection, isDevMode } from '@angular/core';
import { provideServiceWorker } from '@angular/service-worker';
import { AppComponent } from './app/app';
bootstrapApplication(AppComponent, {
  providers: [provideZonelessChangeDetection(), provideServiceWorker('ngsw-worker.js', {
    enabled: !isDevMode() && !('Capacitor' in window), registrationStrategy: 'registerWhenStable:30000'
  })]
}).catch(error => console.error('Application startup failed', error));
