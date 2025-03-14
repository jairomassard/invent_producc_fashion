<template>
  <div>
    <h1>Consulta de Inventario de Productos</h1>

    <div>
      <!-- Contenido de la página -->
      <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button>
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Filtro y Botón Consultar Inventario -->
    <div>
      <!-- Campo de búsqueda por nombre -->
      <div>
        <label for="nombreFiltro">Buscar por nombre:</label>
        <input 
          type="text" 
          id="nombreFiltro"
          v-model="nombreDigitado"
          placeholder="Ingrese nombre del producto"
          class="form-control"
          @input="sincronizarPorNombre"
        />
      </div>

      <!-- Campo de búsqueda por código -->
      <div>
        <label for="codigoFiltro">Buscar por código:</label>
        <input 
          v-model="codigoDigitado" 
          id="codigoFiltro" 
          placeholder="Ingrese código de producto" 
          class="form-control"
          @input="sincronizarCodigoConSelector"
        />
      </div>

      <!-- Selector de productos -->
      <div>
        <label for="productoSelector">Seleccione un producto:</label>
        <select v-model="filtroProducto" id="productoSelector" @change="sincronizarSelectorConCodigo">
          <option value="">Todos</option>
          <option 
            v-for="producto in productosDisponibles" 
            :key="producto.codigo" 
            :value="producto.codigo"
          >
            {{ producto.codigo }} - {{ producto.nombre }}
          </option>
        </select>
      </div>

      <div>
        <button @click="consultar">Consultar Inventario</button>
      </div>
    </div>

    <!-- Tabla de Inventario -->
    <div v-if="mostrarInventario">
      <h2>Inventario de Productos</h2>
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Total</th>
            <th v-for="bodega in bodegas" :key="bodega">{{ bodega }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="producto in productos" :key="producto.codigo">
            <td>{{ producto.codigo }}</td>
            <td>{{ producto.nombre }}</td>
            <td>{{ producto.cantidad_total }}</td>
            <td v-for="bodega in bodegas" :key="bodega">
              {{ producto.cantidades_por_bodega[bodega] || 0 }}
            </td>
          </tr>
        </tbody>
      </table>
      <!-- Controles de paginación -->
      <div v-if="filtroProducto === '' && codigoDigitado === ''">
        <button :disabled="paginaActual === 1" @click="cambiarPagina(paginaActual - 1)">Anterior</button>
        <span>Página {{ paginaActual }}</span>
        <button :disabled="productos.length < limite" @click="cambiarPagina(paginaActual + 1)">Siguiente</button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from "../services/axios";

export default {
  name: "ConsultaInventario",
  data() {
    return {
      filtroProducto: "",
      codigoDigitado: "",
      nombreDigitado: "", // ✅ Nuevo campo para búsqueda por nombre
      productosDisponibles: [],
      productos: [],
      bodegas: [],
      mostrarInventario: false,
      paginaActual: 1, // Página actual
      limite: 20, // Cantidad de productos por página
    };
  },
  methods: {
    limpiarPagina() {
      // 🔹 Limpiar los campos de búsqueda
      this.codigoDigitado = "";
      this.nombreDigitado = ""; // ✅ Limpia el campo de búsqueda por nombre
      this.filtroProducto = "";

      // 🔹 Limpiar la tabla de inventario
      this.productos = [];
      this.bodegas = [];
      this.mostrarInventario = false;

      // 🔹 Reiniciar paginación
      this.paginaActual = 1;
    },

    async consultar() {
      if (this.filtroProducto || this.codigoDigitado) {
        await this.consultarProductoEspecifico();
      } else {
        await this.consultarTodosLosProductos();
      }
    },
    async consultarProductoEspecifico() {
      try {
        const codigo = this.codigoDigitado || this.filtroProducto;
        const response = await apiClient.get(`/api/inventario/${codigo}`);
        const { producto, inventario, message } = response.data;

        if (message) {
          alert(message);
          this.mostrarInventario = false;
          this.productos = [];
          this.bodegas = [];
          return;
        }

        // Obtener todas las bodegas existentes
        const bodegasResponse = await apiClient.get("/api/bodegas");
        const todasLasBodegas = bodegasResponse.data.map((b) => b.nombre);

        // Construir datos para la tabla
        this.bodegas = todasLasBodegas;
        this.productos = [
          {
            codigo: producto.codigo,
            nombre: producto.nombre,
            cantidad_total: inventario.reduce((total, item) => total + item.cantidad, 0),
            cantidades_por_bodega: todasLasBodegas.reduce((acc, bodega) => {
              const item = inventario.find((i) => i.bodega === bodega);
              acc[bodega] = item ? item.cantidad : 0;
              return acc;
            }, {}),
          },
        ];
        this.mostrarInventario = true;
      } catch (error) {
        console.error("Error al consultar inventario específico:", error);
        alert("Ocurrió un error al consultar el inventario del producto.");
      }
    },
    async consultarTodosLosProductos() {
      try {
        const offset = (this.paginaActual - 1) * this.limite;
        const response = await apiClient.get(`/api/inventario?offset=${offset}&limit=${this.limite}`);
        const { productos, bodegas } = response.data;

        // Validar respuesta del backend
        if (!productos || productos.length === 0) {
          alert("No se encontró información en el inventario.");
          this.mostrarInventario = false;
          return;
        }

        // Guardar bodegas y construir datos para la tabla
        this.bodegas = bodegas || [];
        this.productos = productos.map((producto) => {
          const cantidadesPorBodega = this.bodegas.reduce((acc, bodega) => {
            acc[bodega] = producto.cantidades_por_bodega[bodega] || 0; // Asignar 0 si no hay inventario en la bodega
            return acc;
          }, {});

          return {
            codigo: producto.codigo,
            nombre: producto.nombre,
            cantidad_total: producto.cantidad_total,
            cantidades_por_bodega: cantidadesPorBodega,
          };
        });

        this.mostrarInventario = true;
      } catch (error) {
        console.error("Error al consultar inventario general:", error);
        alert("Ocurrió un error al consultar el inventario general.");
      }
    },
    async cargarProductosDisponibles() {
      try {
        const response = await apiClient.get("/api/productos/completos");
        this.productosDisponibles = response.data
          .sort((a, b) => a.codigo.localeCompare(b.codigo)); // Ordenar por código ascendente
      } catch (error) {
        console.error("[ERROR] Al cargar productos disponibles:", error);
      }
    },
    cambiarPagina(nuevaPagina) {
      this.paginaActual = nuevaPagina;
      this.consultarTodosLosProductos(); // Volver a consultar con la nueva página
    },
    sincronizarPorNombre() {
      const productoEncontrado = this.productosDisponibles.find(p => 
        p.nombre.toLowerCase().includes(this.nombreDigitado.toLowerCase())
      );

      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.codigoDigitado = productoEncontrado.codigo;
      }
    },

    sincronizarCodigoConSelector() {
      const productoEncontrado = this.productosDisponibles.find(p => p.codigo === this.codigoDigitado);
      if (productoEncontrado) {
        this.filtroProducto = productoEncontrado.codigo;
        this.nombreDigitado = productoEncontrado.nombre;
      }
    },

    sincronizarSelectorConCodigo() {
      const productoSeleccionado = this.productosDisponibles.find(p => p.codigo === this.filtroProducto);
      if (productoSeleccionado) {
        this.codigoDigitado = productoSeleccionado.codigo;
        this.nombreDigitado = productoSeleccionado.nombre;
      }
    },

    volverAlMenu() {
        this.$router.push('/menu-operador');
    },
  },
  mounted() {
    this.cargarProductosDisponibles();
  },

};
</script>

<style scoped>
/* Contenedor principal */
.consulta-inventario {
  margin: 20px auto;
  max-width: 1200px;
  font-family: Arial, sans-serif;
  padding: 10px;
}

/* Títulos */
h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

h2 {
  color: #0056b3;
  margin-bottom: 15px;
}

/* Botones */
button {
  padding: 0.6rem 1.2rem;
  border: none;
  background-color: #007bff;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  margin-right: 10px;
}

button:hover {
  background-color: #0056b3;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
}

.btn-warning {
  background-color: #ffc107;
  color: #000;
}

.btn-warning:hover {
  background-color: #e0a800;
}

/* Formularios y filtros */
label {
  font-weight: bold;
  display: block;
  margin-bottom: 5px;
  color: #555;
}

select, input {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

/* Tablas */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  font-size: 14px;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background-color: #f8f9fa;
  color: #333;
  font-weight: bold;
}

tbody tr:nth-child(odd) {
  background-color: #f9f9f9;
}

tbody tr:hover {
  background-color: #f1f1f1;
}

/* Secciones */
section {
  margin-bottom: 30px;
  padding: 15px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background-color: #f8f9fa;
}

/* Historial de entregas */
p {
  margin: 5px 0;
  color: #555;
  font-size: 14px;
}

/* --- Responsividad --- */
@media (max-width: 768px) {
  .consulta-inventario {
    margin: 10px auto;
    padding: 10px;
  }

  select, input, button {
    width: 100%;
    margin-bottom: 10px;
    font-size: 16px;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  th, td {
    font-size: 12px;
    padding: 8px;
  }

  h1 {
    font-size: 20px;
  }

  h2 {
    font-size: 18px;
  }
}
</style>
