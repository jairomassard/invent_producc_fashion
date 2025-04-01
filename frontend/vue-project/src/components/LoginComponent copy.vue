<template>
  <div id="login">
    <div class="header-image">
      <img src="/images/cabezote.jpg" alt="Cabezote" class="img-fluid w-100" />
    </div>

    <div class="login-container">
      
      <h2 class="text-center">Inventarios y Producción</h2>
      <h3 class="text-center mb-4">Inicio de Sesión</h3>

      <form @submit.prevent="login">
        <div class="form-group">
          <input
            type="text"
            v-model="usuario"
            class="form-control"
            placeholder="Usuario"
            required
          />
        </div>
        <div class="form-group">
          <input
            type="password"
            v-model="password"
            class="form-control"
            placeholder="Contraseña"
            required
          />
        </div>
        <button type="submit" class="btn btn-primary w-100">Ingresar</button>
      </form>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script>
import apiClient from "../services/axios";

export default {
  data() {
    return {
      usuario: '',
      password: '',
      errorMessage: '',
    };
  },
  methods: {
    async login() {
      try {
        // Hacer la solicitud al endpoint de login
        const response = await apiClient.post('/api/login', {
          usuario: this.usuario,
          password: this.password,
        });

        // Extraer datos de la respuesta
        const { tipo_usuario, id, nombres, apellidos, token } = response.data;

        // Validar que el token está presente en la respuesta
        if (!token) {
          this.errorMessage = 'Token no recibido. Contacta al administrador.';
          console.error('Error: No se recibió un token en la respuesta del backend.');
          return;
        }

        // Almacenar datos en localStorage
        localStorage.setItem('tipo_usuario', tipo_usuario);
        localStorage.setItem('usuario_id', id);
        localStorage.setItem('nombres', nombres);
        localStorage.setItem('apellidos', apellidos);
        localStorage.setItem('token', token);
        console.log('DEBUG: Token almacenado:', token);

        
        // Emitir evento de éxito
        this.$emit('loginSuccess');

        // Redirigir según el tipo de usuario
        if (tipo_usuario === 'admin') {
          this.$router.push('/menu');
        } else if (tipo_usuario === 'gerente') {
          this.$router.push('/menu-gerente');
        } else if (tipo_usuario === 'operador') {
          this.$router.push('/menu-operador');
        } else {
          this.errorMessage = 'Rol no reconocido. Contacta al administrador.';
        }
      } catch (error) {
        // Manejo de errores
        console.error('Error en el inicio de sesión:', error);
        if (error.response?.status === 403) {
          // 🚨 Error por límite de sesiones concurrentes
          alert("Límite de sesiones alcanzado. Intenta más tarde.");
        } else if (error.response?.status === 409) {
          // 🚨 Error por usuario inactivo
          alert("Este usuario está inactivo. Contacta al administrador.");
        } else if (error.response?.status === 401) {
          // 🚨 Error por credenciales incorrectas
          this.errorMessage = "Credenciales incorrectas. Verifica tu usuario y contraseña.";
        } else {
          this.errorMessage =
            error.response?.data?.message || "Error al iniciar sesión. Por favor, inténtalo de nuevo.";
        }
      }
    },
  },
};
</script>

<style scoped>
/* Imagen de encabezado */
.header-image img {
  width: 100%;
  height: auto;
  border-bottom: 4px solid #007bff; /* Barra decorativa */
}

/* Contenedor principal del Login */
.login-container {
  max-width: 400px;
  margin: 30px auto;
  padding: 30px;
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
}

h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 15px;
  font-weight: bold;
}

h3 {
  font-size: 18px;
  color: #555;
  margin-bottom: 20px;
  font-weight: normal;
}

/* Inputs del formulario */
.form-group {
  margin-bottom: 20px;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 14px;
  font-family: Arial, sans-serif;
  transition: border-color 0.3s;
}

.form-control:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
}

/* Botón de inicio de sesión */
button {
  padding: 10px;
  font-size: 16px;
  font-weight: bold;
  border: none;
  border-radius: 5px;
  background-color: #007bff;
  color: #fff;
  cursor: pointer;
  width: 100%;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #0056b3;
}

/* Mensaje de error */
.error-message {
  margin-top: 15px;
  color: #dc3545;
  font-size: 14px;
  font-weight: bold;
}

/* Responsividad */
@media (max-width: 576px) {
  .login-container {
    padding: 20px;
  }

  h2 {
    font-size: 20px;
  }

  h3 {
    font-size: 16px;
  }
}
</style>
