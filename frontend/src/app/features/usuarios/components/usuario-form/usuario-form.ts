import { Component, EventEmitter, inject, Input, OnChanges, Output, SimpleChanges, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import {
  ModificarUsuarioRequest,
  RegistrarUsuarioRequest,
  Rol,
  Usuario,
} from '../../models/usuario.models';

@Component({
  selector: 'app-usuario-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './usuario-form.html',
  styleUrl: './usuario-form.css',
})
export class UsuarioFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() modo: 'crear' | 'editar' = 'crear';
  @Input() usuario: Usuario | null = null;
  @Input() roles: Rol[] = [];
  @Input() guardando = false;
  @Input() erroresServidor: Record<string, string[]> = {};

  @Output() guardar = new EventEmitter<
    RegistrarUsuarioRequest | ModificarUsuarioRequest
  >();

  @Output() cancelar = new EventEmitter<void>();

  readonly mostrarContrasena = signal(false);

  readonly formulario = this.fb.nonNullable.group({
    nombre: ['', [
      Validators.required,
      Validators.maxLength(100),
      Validators.pattern(/^[\p{L}]+(?:[ '\-\u2019][\p{L}]+)*$/u),
    ]],
    email: ['', [
      Validators.required,
      Validators.email,
      Validators.maxLength(50),
    ]],
    direccion: ['', [Validators.maxLength(255)]],
    telefono: ['', [Validators.maxLength(15)]],
    rol_id: [0, [Validators.min(1)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['modo']) {
      const password = this.formulario.controls.password;

      if (this.modo === 'editar') {
        password.disable();
      } else {
        password.enable();
      }
    }

    if (changes['usuario'] && this.usuario) {
      this.formulario.patchValue({
        nombre: this.usuario.nombre,
        email: this.usuario.email,
        direccion: this.usuario.direccion ?? '',
        telefono: this.usuario.telefono ?? '',
        rol_id: this.usuario.rol.rol_id,
      });
    }
  }

  errorCampo(campo: string): string | null {
    const erroresApi = this.erroresServidor[campo];

    if (erroresApi?.length) {
      return erroresApi[0];
    }

    const control = this.formulario.get(campo);

    if (!control || !control.touched || !control.invalid) {
      return null;
    }

    if (control.hasError('required') || control.hasError('min')) {
      return 'Este campo es obligatorio.';
    }

    if (control.hasError('email')) {
      return 'Ingresa un correo electrónico válido.';
    }

    if (control.hasError('minlength')) {
      return 'La contraseña debe tener al menos 8 caracteres.';
    }

    if (control.hasError('maxlength')) {
      return 'El texto supera la longitud permitida.';
    }

    if (control.hasError('pattern')) {
      return 'El nombre solo puede contener letras y espacios.';
    }

    return 'Revisa el valor ingresado.';
  }

  enviarFormulario(): void {
    if (this.guardando) {
      return;
    }

    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();

    const datos = {
      nombre: valores.nombre.trim(),
      email: valores.email.trim().toLowerCase(),
      direccion: valores.direccion.trim() || null,
      telefono: valores.telefono.trim() || null,
      rol_id: valores.rol_id,
    };

    if (this.modo === 'crear') {
      this.guardar.emit({
        ...datos,
        password: valores.password,
      });
    } else {
      this.guardar.emit(datos);
    }
  }
}
