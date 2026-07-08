import { Routes } from '@angular/router';
import { Landing } from './pages/landing/landing';
import { Download } from './pages/download/download';

export const routes: Routes = [
  { path: '', component: Landing, title: 'Relay — messagerie dans le terminal' },
  { path: 'telecharger', component: Download, title: 'Télécharger · Relay' },
  { path: '**', redirectTo: '' },
];
