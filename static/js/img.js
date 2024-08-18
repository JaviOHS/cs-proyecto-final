function MostrarImagenSeleccionada() {
    const selectedImg = document.getElementById('selected-img');
    const inputArchive = document.getElementById('id_image');

    selectedImg.addEventListener('click', () => {
        inputArchive.click();
    });

    inputArchive.style.display = 'none';

    inputArchive.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                selectedImg.src = e.target.result; 
            }
            reader.readAsDataURL(file);
        }
    });
}

document.addEventListener('DOMContentLoaded', MostrarImagenSeleccionada);
