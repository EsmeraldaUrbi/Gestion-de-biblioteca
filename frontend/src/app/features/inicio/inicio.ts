import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { ApiService } from '../../core/services/api';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div style="padding: 20px; font-family: sans-serif;">
      <h1>Sistema de Gestión de Biblioteca</h1>
      <div style="padding: 15px; background: #e0f7fa; border-radius: 5px;">
        <strong>Respuesta de Django:</strong> {{ mensajeBackend }}
      </div>
    </div>
  `
})
export class InicioComponent implements OnInit {
  private apiService = inject(ApiService);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef); // Inyectamos el detector de cambios
  mensajeBackend = 'Cargando...';

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.apiService.getSystemStatus().subscribe({
        next: (res: any) => {
          this.mensajeBackend = res.message;
          this.cdr.detectChanges(); // Forzamos a Angular a pintar el texto en la pantalla inmediatamente
        },
        error: (err) => {
          console.error("Error en la petición:", err);
          this.mensajeBackend = 'Error al conectar con el backend';
          this.cdr.detectChanges();
        }
      });
    }
  }
}