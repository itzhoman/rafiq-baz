import type { CapacitorConfig } from '@capacitor/cli';
const config: CapacitorConfig = {
  appId: 'com.rafiqbaz.app',
  appName: 'رفیق باز',
  webDir: 'dist',
  backgroundColor: '#09090b',
  android: { backgroundColor: '#09090b', allowMixedContent: false },
  ios: { backgroundColor: '#09090b', contentInset: 'automatic', preferredContentMode: 'mobile' }
};
export default config;
