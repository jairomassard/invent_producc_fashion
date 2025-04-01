<template>
  <div id="login">
    <div class="header-image">
      <img src="/images/cabezote.jpg" alt="Cabezote" class="img-fluid w-100" />
    </div>

    <div class="login-wrapper">
      <div class="login-container">
        <h2 class="text-center">Inventarios y Producción</h2>
        <h3 class="text-center mb-4">Inicio de Sesión</h3>

        <form @submit.prevent="login">
          <div class="form-group">
            <div class="input-wrapper">
              <font-awesome-icon icon="user" class="input-icon" />
              <input
                type="text"
                v-model="usuario"
                class="form-control with-icon"
                placeholder="Usuario"
                required
              />
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <font-awesome-icon icon="lock" class="input-icon" />
              <input
                :type="showPassword ? 'text' : 'password'"
                v-model="password"
                class="form-control with-icon"
                placeholder="Contraseña"
                required
              />
              <font-awesome-icon
                :icon="showPassword ? 'eye-slash' : 'eye'"
                class="toggle-password"
                @click="togglePassword"
              />
            </div>
          </div>
          <button type="submit" class="btn btn-primary w-100">
            <font-awesome-icon icon="sign-in-alt" /> Ingresar
          </button>
        </form>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from "../services/axios";

export default {
  data() {
    return {
      usuario: '',
 stiffpassword: '',
      errorMessage: '',
      showPassword: false,
    };
  },
  methods: {
    async login() {
      try {
        const response = await apiClient.post('/api/login', {
          usuario: this.usuario,
          password: this.password,
        });

        const { tipo_usuario, id, nombres, apellidos, token } = response.data;

        if (!token) {
          this.errorMessage = 'Token no recibido. Contacta al administrador.';
          console.error('Error: No se recibió un token en la respuesta del backend.');
          return;
        }

        localStorage.setItem('tipo_usuario', tipo_usuario);
        localStorage.setItem('usuario_id', id);
        localStorage.setItem('nombres', nombres);
        localStorage.setItem('apellidos', apellidos);
        localStorage.setItem('token', token);
        console.log('DEBUG: Token almacenado:', token);

        this.$emit('loginSuccess');

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
        console.error('Error en el inicio de sesión:', error);
        if (error.response?.status === 403) {
          alert("Límite de sesiones alcanzado. Intenta más tarde.");
        } else if (error.response?.status === 409) {
          alert("Este usuario está inactivo. Contacta al administrador.");
        } else if (error.response?.status === 401) {
          this.errorMessage = "Credenciales incorrectas. Verifica tu usuario y contraseña.";
        } else {
          this.errorMessage =
            error.response?.data?.message || "Error al iniciar sesión. Por favor, inténtalo de nuevo.";
        }
      }
    },
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
  },
};
</script>

<style scoped>
/* Contenedor principal */
#login {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Imagen de encabezado */
.header-image img {
  width: 100%;
  height: auto;
  border-bottom: 4px solid #007bff;
}

/* Contenedor para centrar el formulario */
.login-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 40px; /* Espacio adicional después del cabezote */
  padding-bottom: 20px; /* Espacio en la parte inferior */
}

/* Contenedor del formulario */
.login-container {
  max-width: 400px;
  width: 100%;
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

/* Grupos de formulario */
.form-group {
  margin-bottom: 20px;
}

/* Contenedor para íconos dentro del input */
.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
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

.with-icon {
  padding-left: 35px; /* Espacio para el ícono */
}

.form-control:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
}

/* Ícono de mostrar/ocultar contraseña */
.toggle-password {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #666;
}

/* Botón de inicio de sesión */
.btn {
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

.btn:hover {
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
    margin: 15px;
  }

  h2 {
    font-size: 20px;
  }

  h3 {
    font-size: 16px;
  }
}
</style>
