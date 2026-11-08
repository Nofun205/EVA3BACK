/**
 * BuildCorp - Manejador de Firma Digital en HTML5 Canvas
 * Permite trazos fluidos tanto en PC (mouse) como en dispositivos móviles / tablets (touch).
 */

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('signaturePad');
    const hiddenInput = document.getElementById('id_firma_digital_data');
    const clearBtn = document.getElementById('clearSignatureBtn');
    const form = document.querySelector('form');

    if (!canvas || !hiddenInput) {
        return;
    }

    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let hasDrawn = false;

    // Ajustar resolución del canvas para pantallas de alta densidad
    function resizeCanvas() {
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * ratio;
        canvas.height = rect.height * ratio;
        ctx.scale(ratio, ratio);
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = '#0f172a';
    }

    // Inicializar tamaño
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    function getCoords(e) {
        const rect = canvas.getBoundingClientRect();
        if (e.touches && e.touches.length > 0) {
            return {
                x: e.touches[0].clientX - rect.left,
                y: e.touches[0].clientY - rect.top
            };
        }
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    function startDrawing(e) {
        e.preventDefault();
        isDrawing = true;
        hasDrawn = true;
        const { x, y } = getCoords(e);
        ctx.beginPath();
        ctx.moveTo(x, y);
    }

    function draw(e) {
        if (!isDrawing) return;
        e.preventDefault();
        const { x, y } = getCoords(e);
        ctx.lineTo(x, y);
        ctx.stroke();
    }

    function stopDrawing() {
        if (isDrawing) {
            isDrawing = false;
            // Actualizar el input oculto con la representación en base64
            hiddenInput.value = canvas.toDataURL('image/png');
        }
    }

    // Eventos Mouse
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);

    // Eventos Touch (Mobile / Tablet)
    canvas.addEventListener('touchstart', startDrawing, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDrawing);

    // Botón Limpiar Firma
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            hiddenInput.value = '';
            hasDrawn = false;
        });
    }

    // Validación antes de enviar el formulario
    if (form) {
        form.addEventListener('submit', function (e) {
            if (!hasDrawn || !hiddenInput.value) {
                e.preventDefault();
                alert('Debe estampar la firma digital en el recuadro antes de continuar.');
            }
        });
    }
});

