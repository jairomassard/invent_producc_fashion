<template>
  <div class="produccion-admin">
    <h1>Módulo de Producción</h1>

    <div>
      <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button>
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Crear nueva orden de producción -->
    <section>
      <h2>Crear Orden de Producción</h2>
      <form @submit.prevent="revisarOrden">
        
        <!-- Campo de búsqueda por nombre -->
        <label for="nombreProducto">Buscar por nombre:</label>
        <input 
          type="text" 
          id="nombreProducto"
          v-model="nombreProductoCompuesto"
          placeholder="Ingrese nombre del producto"
          class="form-control"
          @input="sincronizarPorNombre"
        />

        <!-- Campo de búsqueda por código -->
        <label for="codigoProducto">Código del Producto:</label>
        <input 
          type="text" 
          id="codigoProducto" 
          v-model="codigoProductoCompuesto" 
          placeholder="Ingrese el código del producto compuesto"
          @input="sincronizarCodigoConSelector"
        />

        <!-- Selector de productos -->
        <label for="producto">Producto Compuesto:</label>
        <select v-model="nuevaOrden.producto_compuesto_id" @change="sincronizarSelectorConCodigo" required>
          <option value="" disabled>Seleccione un producto</option>
          <option v-for="producto in productosCompuestos" :key="producto.id" :value="producto.id">
            {{ producto.codigo }} - {{ producto.nombre }}
          </option>
        </select>

      
        <br>
        <label for="cantidad">Cantidad de Paquetes a Producir:</label>
        <input type="number" v-model="nuevaOrden.cantidad_paquetes" required min="1" />

        <!-- Selector de bodega de producción -->
        <label for="bodegaProduccion">Bodega de Producción:</label>
        <select v-model="nuevaOrden.bodega_produccion" required>
          <option value="" disabled>Seleccione una bodega</option>
          <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.id">
            {{ bodega.nombre }}
          </option>
        </select>

        <br>
        <button type="submit">Revisar</button>
      </form>
    </section>

    <!-- Tabla de revisión -->
    <section v-if="tablaRevisarVisible">
      <h3>Revisión de Componentes</h3>
      <table>
        <thead>
          <tr>
            <th>Componentes</th>
            <th>Cant. x Paquete</th>
            <th>Cant. a Producir</th>
            <th>Cant. Total Req.</th>
            <th>Peso Unitario</th>
            <th>Peso Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="componente in componentes" :key="componente.id">
            <td>{{ componente.nombre }}</td>
            <td>{{ componente.cantidad_requerida }}</td>
            <td>{{ nuevaOrden.cantidad_paquetes }}</td>
            <td>{{ componente.cantidad_total }}</td>
            <td>{{ componente.peso_unitario }}</td>
            <td>{{ componente.peso_total }}</td>
          </tr>
        </tbody>
      </table>

      <button @click="crearOrden">Crear Orden</button>
    </section>

    <!-- Consultar órdenes de producción -->
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

      <!-- Tabla de órdenes de producción -->
      <table v-if="ordenes.length > 0">
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
              <button v-if="orden.estado === 'Pendiente'" @click="actualizarEstado(orden.id, 'Lista para Producción')">
                Marcar Lista para Producción
              </button>
              <button v-if="orden.estado === 'Lista para Producción'" @click="actualizarEstado(orden.id, 'En Producción')">
                Iniciar Producción
              </button>
              <button v-if="orden.estado === 'En Producción' || orden.estado === 'En Producción-Parcial'" @click="registrarProduccion(orden.id)">
                Registrar Producción
              </button>
              <button v-if="orden.estado === 'Pendiente' || orden.estado === 'Lista para Producir'"
                      @click="eliminarOrden(orden.id)" class="btn btn-danger">
                Eliminar Orden
              </button>
              <button @click="cargarDetalleOrden(orden.id)">Detalle</button>
              <button @click="descargarPdf(orden.id)">Imprimir <i class="fas fa-file-pdf pdf-icon"></i></button> <!-- Botón de PDF -->
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="ordenes.length === 0">No se encontraron órdenes de producción.</p>
    </section>

    <section v-if="tablaDetalleVisible">
      <h2>Detalle de la Orden</h2>
      <!-- Botón condicional según el estado de la orden -->
      <button v-if="detalleOrden?.estado === 'Pendiente'" @click="actualizarEstado(detalleOrden.id, 'Lista para Producción')">
        Marcar Lista para Producción
      </button>
      <button v-if="detalleOrden?.estado === 'Lista para Producción'" @click="actualizarEstado(detalleOrden.id, 'En Producción')">
        Iniciar Producción
      </button>
      <button v-if="detalleOrden?.estado === 'En Producción' || detalleOrden?.estado === 'En Producción-Parcial'" @click="registrarProduccion(detalleOrden.id)">
        Registrar Producción
      </button>
      <button v-if="detalleOrden?.estado === 'Pendiente' || detalleOrden?.estado === 'Lista para Producción'" @click="eliminarOrden(detalleOrden.id)" class="btn btn-danger">
        Eliminar Orden
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
            
         <!-- Botón de Entrega Total (solo en estado "En Producción") -->
        <button v-if="detalleOrden.estado === 'En Producción'" @click="realizarEntregaTotal">
          Entrega Total
        </button>

        <!-- 🔹 Nuevo Botón: Cierre Forzado (solo en "En Producción-Parcial") -->
        <!--<button v-if="detalleOrden.estado === 'En Producción-Parcial'" @click="confirmarCierreForzado">
          Cierre Forzado
        </button>  -->

        <!-- 🔹 Botón para habilitar la entrada del comentario -->
        <button v-if="detalleOrden.estado === 'En Producción-Parcial'" @click="habilitarCierreForzado">
          Cierre Forzado
        </button>

        <!-- 🔹 Área de comentario y botón de cierre -->
        <div v-if="cierreForzadoHabilitado">
          <textarea v-model="comentarioCierreForzado" placeholder="Ingrese un comentario (opcional)"></textarea>
          <button @click="confirmarCierreForzado">Confirmar Cierre</button>
        </div>


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
      productosCompuestos: [],
      bodegas: [], // Lista de bodegas disponibles
      nuevaOrden: {
        producto_compuesto_id: null,
        cantidad_paquetes: null,
        bodega_produccion: null, // Nueva propiedad para almacenar la bodega de producción
      },
      codigoProductoCompuesto: "", // Campo de código del producto
      nombreProductoCompuesto: "", // ✅ Nuevo campo para búsqueda por nombre
      filtroEstado: "", // Filtro por estado
      filtroNumeroOrden: "", // Filtro por número de orden
      ordenes: [],
      tablaRevisarVisible: false,
      componentes: [],
      detalleOrden: {}, // Para manejar el detalle de una orden
      tablaDetalleVisible: false, // Mostrar u ocultar la tabla de detalle
      historialEntregas: [],
      cantidadParcial: 0, // Cantidad ingresada por el operador
      comentarioParcial: "", // Comentario opcional
      cantidadPendiente: 0, // Calculada a partir de entregas
      entregasTotales: 0, // Suma de entregas parciales
      entregaParcialHabilitada: false,
      mostrarDetalle: false,
      cierreForzadoHabilitado: false,  // Controla si se muestra el textarea
      comentarioCierreForzado: "",  // Almacena el comentario del usuario
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
      // 🔹 Limpiar la sección "Crear Orden de Producción"
      this.nuevaOrden = {
        producto_compuesto_id: null,
        cantidad_paquetes: null,
        bodega_produccion: null,
      };
      this.codigoProductoCompuesto = "";
      this.nombreProductoCompuesto = "";

      // 🔹 Limpiar la sección de consulta de órdenes de producción
      this.filtroEstado = "";
      this.filtroNumeroOrden = "";
      this.ordenes = [];

      // 🔹 Limpiar la sección de revisión de componentes
      this.tablaRevisarVisible = false;
      this.componentes = [];

      // 🔹 Limpiar la sección de detalle de la orden
      this.detalleOrden = {};
      this.tablaDetalleVisible = false;

      // 🔹 Limpiar historial de entregas y datos de producción
      this.historialEntregas = [];
      this.cantidadParcial = 0;
      this.comentarioParcial = "";
      this.cantidadPendiente = 0;
      this.entregasTotales = 0;
      this.entregaParcialHabilitada = false;
      this.mostrarDetalle = false;
      this.cierreForzadoHabilitado = false;
      this.comentarioCierreForzado = "";

      // ✅ Recargar los productos y bodegas para mantener actualizados los datos disponibles
      this.cargarProductosCompuestos();
      this.cargarBodegas();
    },

    sincronizarCodigoConSelector() {
      const productoEncontrado = this.productosCompuestos.find(
        (p) => p.codigo === this.codigoProductoCompuesto
      );
      if (productoEncontrado) {
        this.nuevaOrden.producto_compuesto_id = productoEncontrado.id;
      }
    },

    sincronizarSelectorConCodigo() {
      const productoSeleccionado = this.productosCompuestos.find(
        (p) => p.id === this.nuevaOrden.producto_compuesto_id
      );
      if (productoSeleccionado) {
        this.codigoProductoCompuesto = productoSeleccionado.codigo;
      }
    },

    async cargarBodegas() {
      try {
        const response = await apiClient.get("/api/bodegas");
        this.bodegas = response.data;
      } catch (error) {
        console.error("Error al cargar las bodegas:", error);
        alert("No se pudieron cargar las bodegas.");
      }
    },

    async cargarProductosCompuestos() {
      try {
        const response = await apiClient.get("/api/productos-compuestos");
        // Ordenar los productos alfabéticamente por el campo nombre
        this.productosCompuestos = response.data
          .sort((a, b) => a.codigo.localeCompare(b.codigo)); // Ordenar productos por código
      } catch (error) {
        console.error("Error al cargar productos compuestos:", error);
        alert("No se pudieron cargar los productos compuestos.");
      }
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

    async revisarOrden() {
      try {
        const response = await apiClient.get(
          `/api/productos-compuestos/detalle?id=${this.nuevaOrden.producto_compuesto_id}`
        );
        this.componentes = response.data.materiales.map((componente) => ({
          nombre: componente.producto_base_nombre,
          cantidad_requerida: componente.cantidad,
          cantidad_total: componente.cantidad * this.nuevaOrden.cantidad_paquetes,
          peso_unitario: componente.peso_unitario,
          peso_total: componente.cantidad * this.nuevaOrden.cantidad_paquetes * componente.peso_unitario,
        }));
        this.tablaRevisarVisible = true;
      } catch (error) {
        console.error("Error al revisar orden:", error);
        alert("No se pudo revisar la orden.");
      }
    },
    async crearOrden() {
        try {
            const usuarioLogueado = localStorage.getItem("usuario_id"); // Asume que el ID del usuario logueado está en localStorage
            const response = await apiClient.post("/api/ordenes-produccion", {
                producto_compuesto_id: this.nuevaOrden.producto_compuesto_id,
                cantidad_paquetes: this.nuevaOrden.cantidad_paquetes,
                bodega_produccion: this.nuevaOrden.bodega_produccion, // Nuevo campo enviado
                creado_por: usuarioLogueado, // Enviar el usuario creador
            });
            alert(response.data.message);
            this.nuevaOrden = {
                producto_compuesto_id: null,
                cantidad_paquetes: null,
                bodega_produccion: null,
            };
            this.consultarOrdenes();
        } catch (error) {
            console.error("Error al crear orden de producción:", error);
            alert("No se pudo crear la orden de producción.");
        }
    },
    async eliminarOrden(ordenId) {
      try {
        // Confirmar la eliminación
        const confirmacion = confirm("¿Estás seguro de que deseas eliminar esta orden?");
        if (!confirmacion) {
          return; // Si el usuario cancela, no hacemos nada
        }

        // Realizar la solicitud al backend para eliminar la orden
        const response = await apiClient.delete(`/api/ordenes-produccion/${ordenId}`);

        alert(response.data.message);

        // Eliminar la orden de la lista en el frontend
        this.ordenes = this.ordenes.filter(orden => orden.id !== ordenId);
      } catch (error) {
        console.error("Error al eliminar la orden:", error);
        alert("No se pudo eliminar la orden.");
      }
    },
    async mostrarDetalleOrden(orden) {
      try {
        const response = await apiClient.get(`/api/ordenes-produccion/${orden.id}`);
        this.ordenDetalle = response.data;
      } catch (error) {
        console.error("Error al obtener el detalle de la orden:", error);
        alert("No se pudo obtener el detalle de la orden.");
      }
    },
    async cargarDetalleOrden(ordenId) {
      try {
        // Obtener los detalles de la orden
        const detalleResponse = await apiClient.get(`/api/ordenes-produccion/${ordenId}`);
        this.detalleOrden = detalleResponse.data.orden || {};
        
        // Asegurar que se asigna el comentario de cierre forzado
        this.detalleOrden.comentario_cierre_forzado = detalleResponse.data.orden.comentario_cierre_forzado || "";

        // ✅ Agregar la bodega de producción sin afectar otras partes
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

        // Marcar la sección de detalle como visible
        this.tablaDetalleVisible = true;
        
      } catch (error) {
        console.error("Error al cargar detalle de la orden:", error);
        alert("No se pudo cargar el detalle de la orden.");
        this.tablaDetalleVisible = false; // Asegurar que la sección se oculte en caso de error
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
    habilitarCierreForzado() {
      this.cierreForzadoHabilitado = true;
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

        //this.cargarDetalleOrden(this.detalleOrden.id); // Actualizar detalles
      

        // Recargar toda la lista de órdenes
        //this.cargarListaOrdenes(); // Asegúrate de que esta función recargue todas las órdenes desde el backend
        // this.consultarOrdenes();

        
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
    async confirmarCierreForzado() {
      try {
        if (!this.detalleOrden || !this.detalleOrden.id) {
          alert("No se puede cerrar la orden porque no se encontró el detalle.");
          return;
        }

        const ordenId = this.detalleOrden.id;

        const confirmacion = confirm(`¿Seguro que deseas cerrar forzadamente la orden ${this.detalleOrden.numero_orden}?`);
        if (!confirmacion) return;

        // Enviar el comentario al backend
        const response = await apiClient.post(`/api/ordenes-produccion/${ordenId}/cierre-forzado`, {
          comentario: this.comentarioCierreForzado
        });

        alert(response.data.message);

        // Limpiar valores después del cierre
        this.cierreForzadoHabilitado = false;
        this.comentarioCierreForzado = "";

        // Recargar la vista con los nuevos cambios
        await this.consultarOrdenes();
        await this.cargarDetalleOrden(ordenId);

      } catch (error) {
        console.error("Error al realizar el Cierre Forzado:", error);
        alert("No se pudo completar el Cierre Forzado.");
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

    sincronizarPorNombre() {
      const productoEncontrado = this.productosCompuestos.find(p => 
        p.nombre.toLowerCase().includes(this.nombreProductoCompuesto.toLowerCase())
      );

      if (productoEncontrado) {
        this.nuevaOrden.producto_compuesto_id = productoEncontrado.id;
        this.codigoProductoCompuesto = productoEncontrado.codigo;
      }
    },

    sincronizarCodigoConSelector() {
      const productoEncontrado = this.productosCompuestos.find(p => p.codigo === this.codigoProductoCompuesto);
      if (productoEncontrado) {
        this.nuevaOrden.producto_compuesto_id = productoEncontrado.id;
        this.nombreProductoCompuesto = productoEncontrado.nombre;
      }
    },

    sincronizarSelectorConCodigo() {
      const productoSeleccionado = this.productosCompuestos.find(p => p.id === this.nuevaOrden.producto_compuesto_id);
      if (productoSeleccionado) {
        this.codigoProductoCompuesto = productoSeleccionado.codigo;
        this.nombreProductoCompuesto = productoSeleccionado.nombre;
      }
    },

    volverAlMenu() {
        const tipoUsuario = localStorage.getItem("tipo_usuario"); // Obtener el tipo de usuario del almacenamiento local

        if (tipoUsuario === "admin") {
          this.$router.push('/menu'); // Redirigir al menú del administrador
        } else if (tipoUsuario === "gerente") {
          this.$router.push('/menu-gerente'); // Redirigir al menú del gerente
        } else {
          alert("Rol no reconocido. Contacta al administrador."); // Manejo de error en caso de un rol desconocido
        }
    },
  },
  mounted() {
    this.cargarProductosCompuestos();
    this.cargarBodegas();
  },
};
</script>

 
<style scoped>
/* Contenedor principal */
.produccion-admin {
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
  .produccion-admin {
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





