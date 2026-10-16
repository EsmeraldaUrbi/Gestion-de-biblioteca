import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import {
  Ejemplar,
  EstadoEjemplar,
  Libro,
} from '../../models/libros.models';
import { EjemplaresService } from '../../services/ejemplares.service';
import { LibrosService } from '../../services/libros.service';

@Component({
  selector: 'app-libro-detalle',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './libro-detalle.html',
  styleUrl: './libro-detalle.css',
})
export class LibroDetalleComponent implements OnInit {
  private readonly librosService = inject(LibrosService);
  private readonly ejemplaresService = inject(EjemplaresService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  libroId!: number;
  readonly pageSize = 10;

  // Estado del libro
  readonly libro = signal<Libro | null>(null);
  readonly cargandoLibro = signal<boolean>(true);
  readonly errorLibro = signal<string | null>(null);

  // Estado de los ejemplares
  readonly ejemplares = signal<Ejemplar[]>([]);
  readonly totalEjemplares = signal<number>(0);
  readonly paginaEjemplares = signal<number>(1);
  readonly cargandoEjemplares = signal<boolean>(true);
  readonly errorEjemplares = signal<string | null>(null);

  // Señales computadas de paginación de ejemplares
  readonly totalPaginasEjemplares = computed(() =>
    Math.max(1, Math.ceil(this.totalEjemplares() / this.pageSize)),
  );

  readonly primerRegistroEjemplar = computed(() =>
    this.totalEjemplares() === 0
      ? 0
      : (this.paginaEjemplares() - 1) * this.pageSize + 1,
  );

  readonly ultimoRegistroEjemplar = computed(() =>
    Math.min(
      this.paginaEjemplares() * this.pageSize,
      this.totalEjemplares(),
    ),
  );

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const id = Number(idParam);

    if (!idParam || isNaN(id) || id <= 0) {
      void this.router.navigateByUrl('/libros');
      return;
    }

    this.libroId = id;
    this.cargarLibro();
    this.cargarEjemplares();

    // Si viene con fragmento #ejemplares, hacer scroll a la sección
    this.route.fragment
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((fragment) => {
        if (fragment === 'ejemplares') {
          setTimeout(() => {
            const el = document.getElementById('seccion-ejemplares');
            el?.scrollIntoView({ behavior: 'smooth' });
          }, 300);
        }
      });
  }

  cargarLibro(): void {
    this.cargandoLibro.set(true);
    this.errorLibro.set(null);

    this.librosService
      .obtener(this.libroId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargandoLibro.set(false)),
      )
      .subscribe({
        next: (libro) => {
          this.libro.set(libro);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 404) {
            this.errorLibro.set('El libro solicitado no existe en el catálogo.');
          } else if (error.status === 401) {
            this.errorLibro.set('Tu sesión ha vencido. Inicia sesión nuevamente.');
          } else if (error.status === 403) {
            this.errorLibro.set('No tienes permiso para consultar este libro.');
          } else if (error.status === 0) {
            this.errorLibro.set('No fue posible conectar con el servidor.');
          } else {
            this.errorLibro.set(
              'No fue posible cargar los datos del libro. Inténtalo nuevamente.',
            );
          }
        },
      });
  }

  cargarEjemplares(): void {
    this.cargandoEjemplares.set(true);
    this.errorEjemplares.set(null);

    this.ejemplaresService
      .listar({
        libro_id: this.libroId,
        page: this.paginaEjemplares(),
        page_size: this.pageSize,
      })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargandoEjemplares.set(false)),
      )
      .subscribe({
        next: (respuesta) => {
          this.ejemplares.set(respuesta.results);
          this.totalEjemplares.set(respuesta.count);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 0) {
            this.errorEjemplares.set(
              'No fue posible conectar con el servidor para consultar ejemplares.',
            );
          } else if (error.status === 401) {
            this.errorEjemplares.set('Tu sesión ha vencido.');
          } else if (error.status === 403) {
            this.errorEjemplares.set(
              'No tienes permiso para consultar ejemplares.',
            );
          } else {
            this.errorEjemplares.set(
              'No fue posible cargar los ejemplares. Inténtalo nuevamente.',
            );
          }
        },
      });
  }

  cambiarPaginaEjemplares(nuevaPagina: number): void {
    if (
      this.cargandoEjemplares() ||
      nuevaPagina < 1 ||
      (this.totalEjemplares() > 0 &&
        nuevaPagina > this.totalPaginasEjemplares()) ||
      nuevaPagina === this.paginaEjemplares()
    ) {
      return;
    }
    this.paginaEjemplares.set(nuevaPagina);
    this.cargarEjemplares();
  }

  formatearFecha(fecha: string | null): string {
    if (!fecha) {
      return 'No registrada';
    }
    return fecha;
  }

  formatearAutores(libro: Libro | null): string {
    if (!libro || !libro.autores || libro.autores.length === 0) {
      return 'Sin autores asignados';
    }
    return libro.autores.map((a) => a.nombre).join(', ');
  }

  obtenerClaseEstado(estado: EstadoEjemplar): string {
    switch (estado) {
      case 'ACTIVO':
        return 'badge--activo';
      case 'MANTENIMIENTO':
        return 'badge--mantenimiento';
      case 'BAJA':
        return 'badge--baja';
      default:
        return '';
    }
  }

  obtenerTextoEstado(estado: EstadoEjemplar): string {
    switch (estado) {
      case 'ACTIVO':
        return 'Activo';
      case 'MANTENIMIENTO':
        return 'Mantenimiento';
      case 'BAJA':
        return 'Baja';
      default:
        return estado;
    }
  }
}
