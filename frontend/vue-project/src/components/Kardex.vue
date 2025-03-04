<template>
  <div class="kardex-view">
    <h1>Kardex de Inventario de Productos</h1>

    <!-- Botones de acción -->
    <div class="actions">
      <button @click="volverAlMenu" class="btn btn-secondary">Volver al Menú Principal</button>
      <button @click="limpiarPagina" class="btn btn-warning">Limpiar Página</button>
    </div>

    <!-- Filtros de búsqueda -->
    <section class="filters">
      <h2>Filtrar Movimientos</h2>
      <div class="filters-header">
        <label for="fechaInicio">Fecha inicio:</label>
        <input type="date" id="fechaInicio" v-model="fechaInicio" />

        <label for="fechaFin">Fecha fin:</label>
        <input type="date" id="fechaFin" v-model="fechaFin" />

        <button @click="consultarKardex" class="btn btn-primary">Consultar Kardex</button>
      </div>

      <div class="filters-products">
        <label for="nombreProducto">Buscar por nombre:</label>
        <input 
          type="text" 
          id="nombreProducto"
          v-model="nombreProducto"
          placeholder="Ingrese nombre del producto"
          class="form-control"
          @input="sincronizarPorNombre"
        />
      </div>
      <div class="filters-products">
        <label for="productoSelector">Seleccione un producto:</label>
        <select v-model="codigoProducto" id="productoSelector" @change="sincronizarSelectorConCodigo">
          <option value="" disabled>Seleccione un producto</option>
          <option v-for="producto in productos" :key="producto.codigo" :value="producto.codigo">
            {{ producto.codigo }} - {{ producto.nombre }}
          </option>
        </select>
      </div>
      <div class="filters-products">
        <label for="codigoProducto">O ingrese el código del producto:</label>
        <input
          type="text"
          id="codigoProducto"
          v-model="codigoProducto"
          placeholder="Ingrese el código del producto"
          class="form-control"
          @input="sincronizarCodigoConSelector"
        />
      </div>

    </section>

    <!-- Mensaje informativo -->
    <p class="info-message">
      Nota: Para incluir movimientos del día actual, seleccione un día adicional como fecha final.
    </p>

    <!-- Filtro por bodega -->
    <section v-if="kardex.length" class="filters-bodega">
      <label for="bodegaSelector">Filtrar por bodega:</label>
      <select v-model="bodegaSeleccionada" id="bodegaSelector" @change="filtrarPorBodega">
        <option value="">Todas las bodegas</option>
        <option v-for="bodega in bodegas" :key="bodega.id" :value="bodega.nombre">
          {{ bodega.nombre }}
        </option>
      </select>
    </section>

    <!-- Tabla de resultados -->
    <section v-if="kardexFiltrado.length" class="results">
      <h2>Movimientos del Producto</h2>
      <div>
        <button @click="imprimirKardexPDF" class="btn btn-success" title="Imprimir PDF"><i class="fas fa-file-pdf pdf-icon"></i></button>
        <button @click="exportarKardexCSV" class="btn btn-info" title="Exportar CSV"><i class="fa-light fa-file-csv csv-icon"></i></button>
        <button @click="exportarKardexExcel" class="btn btn-primary" title="Exportar Excel"><i class="fas fa-file-excel excel-icon"></i></button> <!-- Nuevo botón -->
      </div>
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Cantidad</th>
              <th>Bodega</th>
              <th>Saldo</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(registro, index) in kardexFiltrado" :key="index">
              <td>{{ registro.fecha }}</td>
              <td>{{ registro.tipo }}</td>
              <td>{{ registro.cantidad }}</td>
              <td>{{ registro.bodega || 'N/A' }}</td>
              <td>{{ registro.saldo }}</td>
              <td>{{ registro.descripcion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button @click="imprimirKardexPDF" class="btn btn-success" title="Imprimir PDF"><i class="fas fa-file-pdf pdf-icon"></i></button>
      <button @click="exportarKardexCSV" class="btn btn-info" title="Exportar CSV"><i class="fa-light fa-file-csv csv-icon"></i></button>
      <button @click="exportarKardexExcel" class="btn btn-primary" title="Exportar Excel"><i class="fas fa-file-excel excel-icon"></i></button> <!-- Nuevo botón -->
    </section>

    <!-- Sin resultados -->
    <section v-else>
      <p>No hay datos para mostrar. Realice una consulta o ajuste el filtro por bodega.</p>
    </section>
  </div>
</template>


  
  <script>
  import apiClient from "../services/axios";
  import * as XLSX from "xlsx"; // Importar SheetJS
  
  export default {
    name: "KardexView",
    data() {
      return {
        productos: [], // Lista de productos para el selector
        bodegas: [], // Lista de bodegas cargadas desde el endpoint
        codigoProducto: "", // Código del producto seleccionado
        nombreProducto: "", // ✅ Nuevo campo para búsqueda por nombre
        fechaInicio: "", // Fecha de inicio del filtro
        fechaFin: "", // Fecha de fin del filtro
        kardex: [], // Datos originales del kardex
        kardexFiltrado: [], // Datos filtrados por bodega
        bodegaSeleccionada: "", // Bodega seleccionada en el filtro
      };
    },
    methods: {
      limpiarPagina() {
        this.codigoProducto = "";
        this.nombreProducto = "";  // ✅ Limpia el campo de búsqueda por nombre
        this.fechaInicio = "";
        this.fechaFin = "";
        this.kardex = [];
        this.kardexFiltrado = [];
        this.bodegaSeleccionada = "";
      },
      async cargarProductos() {
        try {
          // Cargar todos los productos sin paginación
          const response = await apiClient.get("/api/productos/completos");
          this.productos = response.data
          .sort((a, b) => a.codigo.localeCompare(b.codigo)) // Ordenar por código ASC
          .map(producto => ({
            codigo: producto.codigo,
            nombre: producto.nombre
          }));
        } catch (error) {
          console.error("Error al cargar productos:", error);
          alert("No se pudieron cargar los productos.");
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
      async consultarKardex() {
        if (!this.codigoProducto || !this.fechaInicio || !this.fechaFin) {
          alert("Debe seleccionar un producto y definir un rango de fechas.");
          return;
        }
  
        try {
          const response = await apiClient.get("/api/kardex", {
            params: {
              codigo: this.codigoProducto,
              fecha_inicio: this.fechaInicio,
              fecha_fin: this.fechaFin,
            },
          });

          if (response.data.message === "No hay movimientos registrados para este producto en el rango de fechas seleccionado.") {
            alert("No hay existencia de este producto en Bodegas.");
            this.kardex = [];
            this.kardexFiltrado = [];
            return;
          }

          this.kardex = response.data.kardex;
          this.kardexFiltrado = [...this.kardex]; // Inicialmente, muestra todos los movimientos
        } catch (error) {
          console.error("Error al consultar el kardex:", error);
          alert("No se pudo consultar el kardex.");
        }
      },
      filtrarPorBodega() {
        if (!this.bodegaSeleccionada) {
          this.kardexFiltrado = [...this.kardex]; // Mostrar todos si no hay filtro
        } else {
          this.kardexFiltrado = this.kardex.filter(
            (mov) => mov.bodega === this.bodegaSeleccionada
          );
        }
      },
      async imprimirKardexPDF() {
        if (!this.codigoProducto || !this.fechaInicio || !this.fechaFin) {
          alert("Debe realizar una consulta antes de generar el PDF.");
          return;
        }

        try {
          const params = {
            codigo: this.codigoProducto,
            fecha_inicio: this.fechaInicio,
            fecha_fin: this.fechaFin,
          };
          // Si hay una bodega seleccionada, añadirla a los parámetros
          if (this.bodegaSeleccionada) {
            params.bodega = this.bodegaSeleccionada;
          }

          const response = await apiClient.get("/api/kardex/pdf", {
            params,
            responseType: "blob",
          });

          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", `kardex_${this.codigoProducto}${this.bodegaSeleccionada ? '_'+this.bodegaSeleccionada : ''}.pdf`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (error) {
          console.error("Error al generar el PDF del Kardex:", error);
          alert("No se pudo generar el PDF del Kardex.");
        }
      },
      exportarKardexCSV() {
        if (!this.kardexFiltrado.length) {
          alert("No hay datos filtrados para exportar a CSV.");
          return;
        }

        let csvContent =
          "data:text/csv;charset=utf-8," +
          `Kardex de Inventario\n` +
          `Producto: ${this.codigoProducto} - ${
            this.productos.find((p) => p.codigo === this.codigoProducto)?.nombre || "Desconocido"
          }\n` +
          `Rango de Fechas: ${this.fechaInicio} a ${this.fechaFin}\n` +
          `Bodega: ${this.bodegaSeleccionada || "Todas"}\n` +
          `Movimientos del Producto:\n\n` +
          `Fecha;Tipo;Cantidad;Bodega;Saldo;Descripción\n`;

        this.kardexFiltrado.forEach((mov) => {
          const fila = [
            mov.fecha,
            mov.tipo,
            mov.cantidad,
            mov.bodega || "N/A",
            mov.saldo,
            mov.descripcion.replace(/;/g, " "),
          ].join(";");
          csvContent += fila + "\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `kardex_${this.codigoProducto}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      },

      exportarKardexExcel() {
        if (!this.kardexFiltrado.length) {
          alert("No hay datos filtrados para exportar a Excel.");
          return;
        }

        // Preparar los datos para el Excel
        const worksheetData = [
          ["Kardex de Inventario"],
          [`Producto: ${this.codigoProducto} - ${this.productos.find((p) => p.codigo === this.codigoProducto)?.nombre || "Desconocido"}`],
          [`Rango de Fechas: ${this.fechaInicio} a ${this.fechaFin}`],
          [`Bodega: ${this.bodegaSeleccionada || "Todas"}`],
          [], // Línea en blanco
          ["Fecha", "Tipo", "Cantidad", "Bodega", "Saldo", "Descripción"], // Encabezados
        ];

        // Agregar los movimientos
        this.kardexFiltrado.forEach((mov) => {
          worksheetData.push([
            mov.fecha,
            mov.tipo,
            mov.cantidad,
            mov.bodega || "N/A",
            mov.saldo,
            mov.descripcion,
          ]);
        });

        // Crear una hoja de trabajo
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Kardex");

        // Exportar el archivo
        XLSX.writeFile(workbook, `kardex_${this.codigoProducto}${this.bodegaSeleccionada ? '_'+this.bodegaSeleccionada : ''}.xlsx`);
      },

      sincronizarPorNombre() {
        const productoEncontrado = this.productos.find((p) => 
          p.nombre.toLowerCase().includes(this.nombreProducto.toLowerCase())
        );

        if (productoEncontrado) {
          this.codigoProducto = productoEncontrado.codigo;
        }
      },

      sincronizarCodigoConSelector() {
        const productoEncontrado = this.productos.find(p => p.codigo === this.codigoProducto);
        if (productoEncontrado) {
          this.nombreProducto = productoEncontrado.nombre;
        }
      },

      sincronizarSelectorConCodigo() {
        const productoEncontrado = this.productos.find(p => p.codigo === this.codigoProducto);
        if (productoEncontrado) {
          this.nombreProducto = productoEncontrado.nombre;
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
      this.cargarProductos();
      this.cargarBodegas(); // Cargar las bodegas al iniciar el componente
    },
  };
  </script>
  
  <style scoped>
  .kardex-view {
    margin: 20px auto;
    max-width: 1200px;
    font-family: Arial, sans-serif;
    padding: 10px;
  }
  .excel-icon {
    font-size: 18px;
    vertical-align: middle;
    margin-left: 5px;
    color: #fff;
  }
  .pdf-icon {
    font-size: 18px;
    vertical-align: middle;
    margin-left: 5px;
    color: #fff;
  }
  .csv-icon {
    font-size: 18px;
    vertical-align: middle;
    margin-left: 5px;
    color: #fff;
  }
  h1 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .actions {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
  }
  
  .filters {
    padding: 15px;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    background-color: #f8f9fa;
    margin-bottom: 20px;
  }
  
  .filters-header {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  .filters-products {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .filters label {
    font-weight: bold;
  }
  
  input,
  select {
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 10px;
  }
  
  .info-message {
    margin-top: 10px;
    font-style: italic;
    color: #555;
  }
  
  .results {
    margin-top: 20px;
  }
  
  .table-responsive {
    overflow-x: auto;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th,
  td {
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
  }
  
  th {
    background-color: #f8f9fa;
  }
  
  tbody tr:hover {
    background-color: #f1f1f1;
  }
  
  button {
    padding: 0.5rem 1rem;
    border: none;
    background-color: #007bff;
    color: #fff;
    cursor: pointer;
    border-radius: 4px;
  }
  
  button:hover {
    background-color: #0056b3;
  }

  button.btn-warning {
    background-color: #ffc107; /* Amarillo para advertencias */
    color: #333; /* Texto oscuro */
  }
  
  button.btn-warning:hover {
    background-color: #e0a800; /* Amarillo más oscuro */
  }
  
  /* Responsivo */
  @media (max-width: 768px) {
    .filters-header {
      flex-direction: column;
    }
  
    table {
      display: block;
      overflow-x: auto;
      white-space: nowrap;
    }
  }
  </style>