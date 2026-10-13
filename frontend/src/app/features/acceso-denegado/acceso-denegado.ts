import {
  Component,
} from '@angular/core';
import {
  RouterLink,
} from '@angular/router';

@Component({
  selector: 'app-acceso-denegado',
  standalone: true,
  imports: [
    RouterLink,
  ],
  templateUrl: './acceso-denegado.html',
  styleUrl: './acceso-denegado.css',
})
export class AccesoDenegadoComponent {}