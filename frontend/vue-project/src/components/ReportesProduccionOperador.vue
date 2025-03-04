<template>
    <div class="reportes-produccion">
      <h1>Reportes de Producción</h1>
  
      <div>
        <!-- Botón para regresar al menú -->
        <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button>
        <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>

      </div>
  
      <!-- Filtros -->
      <section>
        <h2>Consultar Órdenes</h2>
  
        <!-- Filtro por Número de Orden -->
        <label for="numero-orden">Número de Orden:</label>
        <input
          type="text"
          id="numero-orden"
          v-model="filtroNumeroOrden"
          placeholder="Número de Orden"
        />
        <br />
  
        <!-- Filtro por Estado -->
        <label for="estado">Estado:</label>
        <select v-model="filtroEstado" id="estado">
          <option value="">Todos</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Lista para Producción">Lista para Producción</option>
          <option value="En Producción">En Producción</option>
          <option value="En Producción-Parcial">En Producción-Parcial</option>
          <option value="Finalizada">Finalizada</option>
        </select>
        <br />
  
        <!-- Filtro por Rango de Fechas -->
        <label for="fecha-inicio">Fecha Inicio:</label>
        <input type="date" id="fecha-inicio" v-model="filtroFechaInicio" />
        <label for="fecha-fin">Fecha Fin:</label>
        <input type="date" id="fecha-fin" v-model="filtroFechaFin" />
        <br />
  
        <!-- Mensaje informativo -->
        <p class="info-message">
          Nota: Para incluir ordenes del día actual, seleccione un día adicional para Fecha Fin.
        </p>
        <!-- Botón Consultar -->
        <button @click="consultarOrdenes">Consultar</button>
        <button @click="imprimirListadoPdf">Imprimir Listado <i class="fas fa-file-pdf pdf-icon"></i></button>

      </section>
  
      <!-- Tabla de órdenes -->
      <section v-if="ordenes.length > 0">
        <h2>Órdenes de Producción</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Número de Orden</th>
              <th>Producto</th>
              <th>Cantidad a Producir</th>
              <th>Estado</th>
              <th>Fecha Estado</th>
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
              <td>{{ obtenerFechaEstado(orden) }}</td>
              <td>
                <button @click="cargarDetalleOrden(orden.id)">Detalle</button>
                <button @click="descargarPdf(orden.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
  
      <p v-if="ordenes.length === 0 && filtroEstado !== '' && filtroNumeroOrden === ''">
        No se encontraron órdenes de producción.
      </p>
  
      <!-- Detalle de la orden -->
      <section v-if="mostrarDetalle">
        <h2>Detalle de la Orden</h2>
        <!-- Información del detalle -->
        <div>
          <button @click="descargarPdf(detalleOrden.id)">Imprimir Detalle en PDF</button>
        </div>
        <!-- Información del detalle -->
        <p><strong>Número de Orden:</strong> {{ detalleOrden.numero_orden }}</p>
        <p><strong>Producto:</strong> {{ detalleOrden.producto_compuesto_nombre }}</p>
        <p><strong>Cantidad de Paquetes:</strong> {{ detalleOrden.cantidad_paquetes }}</p>
        <p><strong>Bodega de Producción:</strong> {{ detalleOrden?.bodega_produccion_nombre || 'No especificada' }}</p>
        <p><strong>Estado:</strong> {{ detalleOrden?.estado || '-' }}</p>
        <p><strong>Fecha de Creación:</strong> {{ formatFecha(detalleOrden.fecha_creacion) }}</p>
        <p><strong>Fecha Lista para Producción:</strong> {{ formatFecha(detalleOrden.fecha_lista_para_produccion) }}</p>
        <p><strong>Fecha Inicio Producción:</strong> {{ formatFecha(detalleOrden.fecha_inicio) }}</p>
        <p><strong>Fecha de Finalización:</strong> {{ formatFecha(detalleOrden.fecha_finalizacion) }}</p>
        <br/>
        
        <table>
            <thead>
                <tr>
                <th>Componente</th>
                <th>Cant. x Paquete</th>
                <th>Cant. Total</th>
                <th>Peso x Paquete</th>
                <th>Peso Total</th>
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

        <!-- Tabla de Historial de Entregas -->
        <h2>Historial de Entregas</h2>
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
        filtroNumeroOrden: "",
        filtroEstado: "",
        filtroFechaInicio: "",
        filtroFechaFin: "",
        ordenes: [],
        detalleOrden: null,
        historialEntregas: [],
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
          // Resetear filtros
          this.filtroNumeroOrden = ""; // Restablecer el filtro por número de orden
          this.filtroEstado = ""; // Restablecer el filtro por estado
          this.filtroFechaInicio = ""; // Limpiar la fecha de inicio
          this.filtroFechaFin = ""; // Limpiar la fecha de fin

          // Limpiar los datos cargados
          this.ordenes = []; // Vaciar la lista de órdenes
          this.detalleOrden = null; // Limpiar el detalle de la orden
          this.historialEntregas = []; // Limpiar el historial de entregas
          this.mostrarDetalle = false; // Ocultar la sección de detalles

          // Opcional: Mostrar un mensaje de que la página ha sido limpiada
          //alert("La página ha sido limpiada correctamente.");
      },
      obtenerFechaEstado(orden) {
        switch (orden.estado) {
          case "Pendiente":
            return this.formatFecha(orden.fecha_creacion);
          case "Lista para Producción":
            return this.formatFecha(orden.fecha_lista_para_produccion);
          case "En Producción":
          case "En Producción-Parcial":
            return this.formatFecha(orden.fecha_inicio);
          case "Finalizada":
            return this.formatFecha(orden.fecha_finalizacion);
          default:
            return "-";
        }
      },
      async consultarOrdenes() {
        try {
            const params = {};

            if (this.filtroNumeroOrden) {
            params.numero_orden = this.filtroNumeroOrden;
            } else {
            if (this.filtroEstado) {
                params.estado = this.filtroEstado;
            }
            if (this.filtroFechaInicio && this.filtroFechaFin) {
                params.fecha_inicio = this.filtroFechaInicio;
                params.fecha_fin = this.filtroFechaFin;
            }
            }

            const response = await apiClient.get("/api/ordenes-produccion/filtrar", { params });
            //this.ordenes = response.data;
            // Ordenar de forma descendente por ID
            this.ordenes = response.data.sort((a, b) => b.id - a.id);

            this.mostrarDetalle = false;
            this.detalleOrden = null;
        } catch (error) {
            console.error("Error al consultar órdenes de producción:", error);
            alert("No se pudieron consultar las órdenes de producción.");
        }
      },
      async imprimirListadoPdf() {
        try {
            const params = {
            estado: this.filtroEstado || null,
            fecha_inicio: this.filtroFechaInicio || null,
            fecha_fin: this.filtroFechaFin || null,
            };

            const response = await apiClient.post("/api/ordenes-produccion/listado-operador-pdf", params, {
            responseType: "blob", // Importante para manejar archivos binarios
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "Listado_Ordenes_Produccion.pdf");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error("Error al imprimir el listado en PDF:", error);
            alert("No se pudo generar el PDF del listado.");
        }
      },
      async cargarDetalleOrden(ordenId) {
        try {
            // Solicitar detalles de la orden
            const detalleResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}`);
            this.detalleOrden = detalleResponse.data.orden || {};
            this.detalleOrden.bodega_produccion_nombre = detalleResponse.data.orden.bodega_produccion_nombre || "No especificada";
            
            // Cargar los materiales asociados (componentes)
            if (detalleResponse.data.materiales) {
            this.componentes = detalleResponse.data.materiales.map((componente) => ({
                nombre: componente.producto_base_nombre,
                cant_x_paquete: componente.cant_x_paquete,
                cantidad_total: componente.cantidad_total,
                peso_x_paquete: componente.peso_x_paquete,
                peso_total: componente.peso_total,
            }));
            } else {
            this.componentes = []; // Asegurarse de limpiar los componentes si no hay datos
            }

            // Solicitar el historial de entregas
            const historialResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}/historial-entregas`);
            this.historialEntregas = historialResponse.data.historial || [];

            // Mostrar el detalle
            this.mostrarDetalle = true;
        } catch (error) {
            console.error("Error al cargar detalle de la orden:", error);
            alert("No se pudo cargar el detalle de la orden.");
            this.mostrarDetalle = false; // Ocultar detalle si hay un error
        }
      },
      async descargarPdf(ordenId) {
        try {
          if (!ordenId) {
            alert("El ID de la orden no está disponible.");
            return;
          }
          const response = await apiClient.get(`/api/ordenes-produccion/${ordenId}/pdf`, {
            responseType: "blob",
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
        const tipoUsuario = localStorage.getItem("tipo_usuario"); // Obtener el tipo de usuario del almacenamiento local

        if (tipoUsuario === "admin") {
          this.$router.push('/menu'); // Redirigir al menú del administrador
        } else if (tipoUsuario === "gerente") {
          this.$router.push('/menu-gerente'); // Redirigir al menú del gerente
        } else if (tipoUsuario === "operador") {
          this.$router.push('/menu-operador'); // Redirigir al menú del gerente
        } else {
          alert("Rol no reconocido. Contacta al administrador."); // Manejo de error en caso de un rol desconocido
        }
      },
    },
  };
  </script>
  
  <style scoped>
  /* Contenedor principal */
  .reportes-produccion {
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

  button.btn-warning {
    background-color: #ffc107; /* Amarillo para advertencias */
    color: #333; /* Texto oscuro */
  }
  
  button.btn-warning:hover {
    background-color: #e0a800; /* Amarillo más oscuro */
  }
  
  /* Formularios */
  form label {
    font-weight: bold;
    display: block;
    margin-bottom: 5px;
    color: #555;
  }
  
  form input, form select {
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
    /* Reducir márgenes en pantallas pequeñas */
    .reportes-produccion {
      margin: 10px auto;
      padding: 10px;
    }
  
    /* Formularios en columna */
    form input, form select, button {
      width: 100%;
      margin-bottom: 10px;
      font-size: 16px;
    }
  
    /* Tablas desplazables horizontalmente */
    table {
      display: block;
      overflow-x: auto;
      white-space: nowrap;
    }
  
    th, td {
      font-size: 12px;
      padding: 8px;
    }
  
    /* Reducir tamaño de títulos */
    h1 {
      font-size: 20px;
    }
  
    h2, h3 {
      font-size: 18px;
    }
  }
  </style>
  