// Apartado de control de fondos para las pestañas
const configuracionFondos = {
    "bienvenida": {
        celular: "/static/fondo_cel.png",
        pc: "/static/fondo_pc.png"
    },
    "dashboard": {
        celular: "/static/fondo_dashboard-cel.png",
        pc: "/static/fondo_dashboard-pc.png"
    },
    "login": {
        celular: "/static/fondo_login-cel.png",
        pc: "/static/fondo_login-pc.png"
    }
};
// Función automática para aplicar el fondo según la pestaña y el tamaño de pantalla
function aplicarFondoPantalla(nombrePestaña) {
    const fondos = configuracionFondos[nombrePestaña];
    if (!fondos) return;

    const esCelular = window.innerWidth <= 768;
    const fondoSeleccionado = esCelular ? fondos.celular : fondos.pc;

    // Aplica el estilo directamente al fondo de la página
    document.body.style.backgroundImage = `url('${fondoSeleccionado}')`;
    document.body.style.backgroundSize = "cover";
    document.body.style.backgroundPosition = "center";
    document.body.style.backgroundAttachment = "fixed";
}