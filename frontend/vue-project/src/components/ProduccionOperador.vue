<template>
  <div class="produccion-operador">
    <h1>Módulo de Producción - Operador</h1>

    <div>
      <!-- Contenido de la página -->
      <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button>
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Filtros -->
    <section>
      <h2>Órdenes de Producción</h2>

      <!-- Filtros -->
      <div>
        <label for="numero-orden">Número de Orden:</label>
        <input
          type="text"
          id="numero-orden"
          v-model="filtroNumeroOrden"
          placeholder="Ingrese el número de orden"
        />

        <label for="estado">Estado:</label>
        <select v-model="filtroEstado" id="estado">
          <option value="">Todos</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Lista para Producción">Lista para Producción</option>
          <option value="En Producción">En Producción</option>
          <option value="En Producción-Parcial">En Producción-Parcial</option>
          <option value="Finalizada">Finalizada</option>
        </select>
        <br>
        <button @click="consultarOrdenes">Consultar</button>
    </div>
    </section>

    <!-- Tabla de órdenes -->
    <section v-if="ordenes.length > 0">
      <h2>Órdenes Disponibles</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Número de Orden</th>
            <th>Producto</th>
            <th>Cantidad a Producir</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="orden in ordenes" :key="orden.id">
            <td>{{ orden.id }}</td>
            <td>{{ orden.numero_orden }}</td>
            <td>{{ orden.producto_compuesto_nombre }}</td>
            <td>{{ orden.cantidad_paquetes }}</td>
            <td>{{ orden.estado }}</td>
            <td>
              <button v-if="orden.estado === 'Lista para Producción'" @click="actualizarEstado(orden.id, 'En Producción')">
                Iniciar Producción
              </button>
              <button v-if="orden.estado === 'En Producción' || orden.estado === 'En Producción-Parcial'" @click="registrarProduccion(orden.id)">
                Registrar Producción
              </button>
              <button @click="cargarDetalleOrden(orden.id)">Detalle</button>
              <button @click="descargarPdf(orden.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button> <!-- Botón de PDF -->
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <p v-if="ordenes.length === 0">No se encontraron órdenes de producción.</p>

    <!-- Detalle de la orden -->
    <section v-if="mostrarDetalle">
      <h2>Detalle de la Orden</h2>
      <!-- Botón condicional según el estado de la orden -->
      <button v-if="detalleOrden?.estado === 'Lista para Producción'" @click="actualizarEstado(detalleOrden.id, 'En Producción')">
        Iniciar Producción
      </button>

      <!-- Botón para imprimir PDF -->
      <button @click="descargarPdf(detalleOrden?.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button>

        
      <p><strong>Número de Orden:</strong> {{ detalleOrden?.numero_orden || 'N/A' }}</p>
      <p><strong>Producto:</strong> {{ detalleOrden?.producto_compuesto_nombre || 'N/A' }}</p>
      <p><strong>Cantidad de Paquetes:</strong> {{ detalleOrden?.cantidad_paquetes || 'N/A' }}</p>
      <p><strong>Bodega de Producción:</strong> {{ detalleOrden?.bodega_produccion_nombre || 'No especificada' }}</p>
      <p><strong>Estado:</strong> {{ detalleOrden?.estado || 'N/A' }}</p>
      <p><strong>Fecha de Creación:</strong> {{ formatFecha(detalleOrden?.fecha_creacion) }}</p>
      <p><strong>Fecha Lista para Producción:</strong> {{ formatFecha(detalleOrden?.fecha_lista_para_produccion) }}</p>
      <p><strong>Fecha Inicio Producción:</strong> {{ formatFecha(detalleOrden?.fecha_inicio) }}</p>
      <p><strong>Fecha de Finalización:</strong> {{ formatFecha(detalleOrden?.fecha_finalizacion) }}</p>
      <p><strong>Creado por:</strong> {{ detalleOrden?.creado_por || 'N/A' }}</p>
      <p><strong>Producido por:</strong> {{ detalleOrden?.producido_por || 'N/A' }}</p>

      <table>
        <thead>
          <tr>
            <th style="width: 60%">Componente</th>
            <th style="width: 10%">Cant. x Paquete</th>
            <th style="width: 10%">Cant. Total</th>
            <th style="width: 10%">Peso x Paquete</th>
            <th style="width: 10%">Peso Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="componente in componentes" :key="componente.nombre">
            <td>{{ componente.nombre }}</td>
            <td>{{ componente.cant_x_paquete }}</td>
            <td>{{ componente.cantidad_total }}</td>
            <td>{{ componente.peso_x_paquete }}</td>
            <td>{{ componente.peso_total }}</td>
          </tr>
        </tbody>
      </table>
    </section>
    
    <!-- Opciones de Producción -->
    <section v-if="detalleOrden && (detalleOrden.estado === 'En Producción' || detalleOrden.estado === 'En Producción-Parcial' || detalleOrden.estado === 'Finalizada') ">
      <h3>Opciones de Producción</h3>
      
      <div v-if="detalleOrden.estado === 'En Producción' || detalleOrden.estado === 'En Producción-Parcial'">
        <!--<button @click="habilitarEntregaParcial":disabled="cantidadPendiente === 0">Entrega Parcial</button>-->
        
        <!-- Botón de Entrega Parcial SIEMPRE disponible en estado "En Producción" o "En Producción-Parcial" -->
        <button @click="habilitarEntregaParcial" :disabled="cantidadPendiente === 0">
          Entrega Parcial
        </button>
            
        <!--<button @click="realizarEntregaTotal">Entrega Total</button>-->
        <button v-if="detalleOrden.estado === 'En Producción'" @click="realizarEntregaTotal">
          Entrega Total
        </button>

      </div>

      <div v-if="entregaParcialHabilitada">
        <label for="cantidad-parcial">Cantidad Parcial a Entregar:</label>
        <input type="number" v-model="cantidadParcial" min="1" :max="cantidadPendiente" />
        <label for="comentario">Comentario (opcional):</label>
        <input type="text" v-model="comentarioParcial" placeholder="Añadir un comentario..." />
        <button @click="registrarEntregaParcial">Entregar</button>
      </div>

      <h3>Historial de Entregas</h3>
      <table v-if="historialEntregas.length > 0">
        <thead>
          <tr>
            <th>Cantidad Entregada</th>
            <th>Fecha y Hora</th>
            <th>Comentario</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entrega in historialEntregas" :key="entrega.id">
            <td>{{ entrega.cantidad }}</td>
            <td>{{ formatFecha(entrega.fecha_hora) }}</td>
            <td>{{ entrega.comentario || 'N/A' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>No hay entregas registradas para esta orden.</p>

      <p><strong>Cantidad Pendiente:</strong> {{ cantidadPendiente }}</p>
      
      <p v-if="detalleOrden.comentario_cierre_forzado">
        <strong>
          <h3>Cierre Forzado: </h3>
                  </strong> {{ detalleOrden.comentario_cierre_forzado }}
      </p>
      <p v-else>
        <strong> 
          <h3>Orden Finalizada sin novedad.</h3>
        </strong>
        
      </p>

    </section>

  </div>
</template>

<script>
import apiClient from "../services/axios";

export default {
  data() {
    return {
      filtroEstado: "",
      filtroNumeroOrden: "", // Filtro por número de orden
      ordenes: [],
      //detalleOrden: null,
      detalleOrden: {},
      componentes: [],
      historialEntregas: [],
      cantidadParcial: 0, // Cantidad ingresada por el operador
      comentarioParcial: "", // Comentario opcional
      cantidadPendiente: 0, // Calculada a partir de entregas
      entregasTotales: 0, // Suma de entregas parciales
      entregaParcialHabilitada: false,
      mostrarDetalle: false,
    };
  },
  methods: {
    formatFecha(fecha) {
      if (!fecha) return "-";
      const fechaObj = new Date(fecha);
      return fechaObj.toLocaleString("es-CO", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    },
    limpiarPagina() {
      // Resetea los valores de los datos de la página
      this.filtroEstado = ""; // Limpia el filtro por estado
      this.filtroNumeroOrden = ""; // Restablecer filtro por número de orden
      this.ordenes = []; // Limpia la lista de órdenes
      this.detalleOrden = {}; // Limpia el detalle de la orden
      this.componentes = []; // Limpia los componentes
      this.historialEntregas = []; // Limpia el historial de entregas
      this.cantidadParcial = 0; // Reinicia la cantidad parcial
      this.comentarioParcial = ""; // Limpia el comentario
      this.cantidadPendiente = 0; // Reinicia la cantidad pendiente
      this.entregasTotales = 0; // Reinicia las entregas totales
      this.entregaParcialHabilitada = false; // Deshabilita la entrega parcial
      this.mostrarDetalle = false; // Oculta los detalles
    },
    async consultarOrdenes() {
      try {
        // Parámetros de filtrado
        let params = {};

        // Agregar filtro por estado si está definido
        if (this.filtroEstado) {
          params.estado = this.filtroEstado;
        }

        // Agregar filtro por número de orden si está definido
        if (this.filtroNumeroOrden) {
          params.numero_orden = this.filtroNumeroOrden;
        }

        // Realizar la petición con los parámetros de filtro
        const response = await apiClient.get("/api/ordenes-produccion", { params });

        // Ordenar de forma descendente por ID
        this.ordenes = response.data.sort((a, b) => b.id - a.id);

        this.mostrarDetalle = false; // Ocultar la sección de detalles al consultar órdenes
        this.detalleOrden = {}; // Limpiar los datos del detalle
      } catch (error) {
        console.error("Error al consultar órdenes de producción:", error);
        alert("No se pudieron consultar las órdenes de producción.");
      }
    },
    async cargarDetalleOrden(ordenId) {
      try {
        // Obtener los detalles de la orden
        const detalleResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}`);
        this.detalleOrden = detalleResponse.data.orden || {};
        this.detalleOrden.bodega_produccion_nombre = detalleResponse.data.orden.bodega_produccion_nombre || "No especificada";

        // Mapear los componentes de la orden
        this.componentes = detalleResponse.data.materiales.map((componente) => ({
          nombre: componente.producto_base_nombre,
          cant_x_paquete: componente.cant_x_paquete,
          peso_x_paquete: componente.peso_x_paquete,
          cantidad_total: componente.cantidad_total,
          peso_total: componente.peso_total,
        }));

        // Obtener el historial de entregas de la orden
        const historialResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}/historial-entregas`);
        this.historialEntregas = historialResponse.data.historial || [];
        this.entregasTotales = historialResponse.data.total_entregado || 0;
        this.cantidadPendiente = historialResponse.data.cantidad_pendiente || 0;

        // NUEVO: Mostrar historial de entregas incluso si la orden está finalizada
        if (this.detalleOrden.estado === "Finalizada" && this.historialEntregas.length > 0) {
          this.mostrarHistorialEntregas = true; // Una bandera adicional si la necesitas
        }

        this.mostrarDetalle = true; // Mostrar el detalle de la orden
      } catch (error) {
        console.error("Error al cargar detalle de la orden:", error);
        alert("No se pudo cargar el detalle de la orden.");
        this.detalleOrden = {}; // Asegurarte de que no sea null
        this.mostrarDetalle = false; // Asegurarte de ocultar el detalle si hay un error
      }
    },
    async actualizarEstado(ordenId, nuevoEstado) { 
      try {
        const usuarioId = localStorage.getItem("usuario_id"); // Obtén el ID del usuario logueado desde localStorage
        
        if (!usuarioId) {
          alert("No se pudo obtener el ID del usuario logueado.");
          return;
        }

        // Realiza la solicitud al backend para actualizar el estado
        const response = await apiClient.put(`/api/ordenes-produccion/${ordenId}/estado`, {
          nuevo_estado: nuevoEstado,
          usuario_id: usuarioId, // Incluye el ID del usuario operador en el cuerpo de la solicitud
        });

        // Mostrar mensaje de éxito
        alert(response.data.message);

        // Actualizar el estado de la orden en la lista
        const orden = this.ordenes.find((orden) => orden.id === ordenId);
        if (orden) {
          orden.estado = nuevoEstado;
          if (nuevoEstado === "Lista para Producción" && !orden.fecha_lista_para_produccion) {
            orden.fecha_lista_para_produccion = new Date().toISOString();
          } else if (nuevoEstado === "En Producción" && !orden.fecha_inicio) {
            orden.fecha_inicio = new Date().toISOString();
          }
        }
        // Esperar la actualización de estado antes de refrescar la vista
        await this.consultarOrdenes();
        await this.cargarDetalleOrden(ordenId);


      } catch (error) {
        console.error("Error al actualizar el estado de la orden:", error);
        alert("No se pudo actualizar el estado de la orden.");
      }
    },
    habilitarEntregaParcial() {
      this.entregaParcialHabilitada = true;
    },
    async registrarEntregaParcial() {
      if (!this.cantidadParcial || this.cantidadParcial <= 0) {
        alert("Por favor, ingrese una cantidad válida.");
        return;
      }

      try {
        const usuarioId = localStorage.getItem("usuario_id");
        if (!usuarioId) {
          alert("No se pudo obtener el ID del usuario logueado.");
          return;
        }

        const response = await apiClient.post(`/api/ordenes-produccion/${this.detalleOrden.id}/entrega-parcial`, {
          cantidad_entregada: this.cantidadParcial,
          comentario: this.comentarioParcial,
          usuario_id: usuarioId,
        });

        alert(response.data.message);
        this.entregaParcialHabilitada = false; // Deshabilitar campo de entrega parcial
        await this.cargarDetalleOrden(this.detalleOrden.id);
        await this.consultarOrdenes();
      
      } catch (error) {
        console.error("Error al registrar entrega parcial:", error);
        alert("No se pudo registrar la entrega parcial.");
      }
    },
    async realizarEntregaTotal() {
      try {
        if (!this.detalleOrden || !this.detalleOrden.id) {
          alert("No se puede finalizar la orden porque no se encontró el detalle.");
          return;
        }

        const ordenId = this.detalleOrden.id; // Guardamos el ID antes de resetear detalleOrden

        const response = await apiClient.post(`/api/ordenes-produccion/${ordenId}/registrar-entrega-total`, {
          nuevo_estado: "Finalizada",
        });

        alert(response.data.message);

        // Esperar la actualización de estado antes de refrescar la vista
        await this.consultarOrdenes();
        await this.cargarDetalleOrden(ordenId); // Usamos la variable temporal

      } catch (error) {
        console.error("Error al finalizar la orden:", error);
        alert("No se pudo finalizar la orden.");
      }
    },
    async registrarProduccion(ordenId) {
      try {
        // Asegurar que el detalle esté cargado
        if (!this.detalleOrden || this.detalleOrden.id !== ordenId) {
          await this.cargarDetalleOrden(ordenId);
        }
        // Mostrar la sección de opciones de producción si la orden está en estado válido
        if (this.detalleOrden.estado === 'En Producción' || this.detalleOrden.estado === 'En Producción-Parcial') {
          this.mostrarDetalle = true;
        } else {
          alert("La orden no está en estado válido para registrar producción.");
        }
      } catch (error) {
        console.error("Error al registrar producción:", error);
        alert("No se pudo mostrar las opciones de producción.");
      }
    },
    async descargarPdf(ordenId) {
      try {
        const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf`, {
          responseType: "blob", // Importante para manejar archivos binarios
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `Orden_${ordenId}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error("Error al descargar el PDF:", error);
        alert("No se pudo descargar el PDF de la orden.");
      }
    },
    volverAlMenu() {
      this.$router.push('/menu-operador');
    },
  },
  mounted() {
    
  },
};
</script>

<style scoped>
/* Contenedor principal */
.produccion-operador {
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

h2, h3 {
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
  .produccion-operador {
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

  h2, h3 {
    font-size: 18px;
  }
}
</style>


