import {
  CommonModule,
} from '@angular/common';
import {
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  ActivatedRoute,
  Router,
  RouterLink,
} from '@angular/router';

import { LibroCatalogo } from '../../models/catalogo.models';
import { CatalogoService } from '../../services/catalogo.service';

@Component({
  selector: 'app-catalogo-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
  ],
  templateUrl: './catalogo-detail.html',
  styleUrl: './catalogo-detail.css',
})
export class CatalogoDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly catalogoService = inject(CatalogoService);

  readonly libro = signal<LibroCatalogo | null>(null);
  readonly cargando = signal<boolean>(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const libroId = idParam ? parseInt(idParam, 10) : null;

    if (!libroId || isNaN(libroId)) {
      this.cargando.set(false);
      this.error.set('Identificador de libro inválido.');
      return;
    }

    this.cargarDetalle(libroId);
  }

  cargarDetalle(libroId: number): void {
    this.cargando.set(true);
    this.error.set(null);

    this.catalogoService.obtenerDetalle(libroId).subscribe({
      next: (libro) => {
        this.libro.set(libro);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        if (err.status === 404) {
          this.error.set('El libro solicitado no existe.');
        } else {
          this.error.set('Ocurrió un error al cargar la información del libro.');
        }
      },
    });
  }

  volver(): void {
    void this.router.navigate(['/catalogo']);
  }

  formatearAutores(libro: LibroCatalogo): string {
    if (!libro.autores || libro.autores.length === 0) {
      return 'Autor no registrado';
    }
    return libro.autores.map((a) => a.nombre).join(', ');
  }
}
