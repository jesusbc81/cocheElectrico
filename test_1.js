// Test ultra-rápido de envío directo
const ENDPOINT = "https://jbc-app-daw-default-rtdb.europe-west1.firebasedatabase.app/hola.json";


// Función para generar números con exactamente 2 decimales
function generarEje(min, max) {
  const numero = Math.random() * (max - min) + min;
  return parseFloat(numero.toFixed(2));
}

// Función auxiliar para esperar un tiempo entre envíos (en milisegundos)
const esperar = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function enviarLoteDeDatos() {
  console.log("🚀 Iniciando el envío de 20 datos aleatorios...");

  for (let i = 1; i <= 20; i++) {
    const datosAceleracion = {
      x: generarEje(-10, 10),
      y: generarEje(-10, 10),
      z: generarEje(-2, 12), // Simula variaciones cercanas a la gravedad terrestre
      timestamp: Date.now()   // Añade el tiempo exacto del envío
    };

    try {
      const respuesta = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datosAceleracion)
      });

      if (respuesta.ok) {
        const resultado = await respuesta.json();
        console.log(`[${i}/20] Guardado ID: ${resultado.name} -> x: ${datosAceleracion.x}, y: ${datosAceleracion.y}, z: ${datosAceleracion.z}`);
      } else {
        console.error(`❌ Error en el dato ${i}:`, respuesta.statusText);
      }
    } catch (error) {
      console.error(`❌ Error de conexión en el dato ${i}:`, error.message);
    }

    // Espera 500 milisegundos (medio segundo) antes de enviar el siguiente dato
    await esperar(500);
  }

  console.log("🏁 ¡Envío de los 20 datos completado!");
}

// Ejecutar el lote completo
enviarLoteDeDatos();
