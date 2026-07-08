import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RevealDirective } from '../../directives/reveal.directive';

@Component({
  selector: 'app-docs',
  imports: [RouterLink, RevealDirective],
  templateUrl: './docs.html',
})
export class Docs {}
