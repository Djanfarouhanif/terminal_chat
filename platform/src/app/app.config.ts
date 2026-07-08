import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withViewTransitions } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(
      routes,
      // Crossfade natif entre les routes (View Transitions API).
      // Le scroll (haut de page + ancres) est géré par Lenis dans App.
      withViewTransitions(),
    ),
    provideHttpClient(),
  ]
};
