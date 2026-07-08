import { Routes } from '@angular/router';
import { Landing } from './pages/landing/landing';
import { Download } from './pages/download/download';

export const routes: Routes = [
  { path: '', component: Landing, title: 'Hanif Chat CLI — messagerie dans le terminal' },
  { path: 'telecharger', component: Download, title: 'Télécharger · Hanif Chat CLI' },
  { path: '**', redirectTo: '' },
];
