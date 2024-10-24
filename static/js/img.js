function MostrarImagenSeleccionada() {
  const selectedImg = document.getElementById('selected-img');
  const inputArchive = document.getElementById('id_image');

  if (selectedImg && inputArchive) {
    selectedImg.addEventListener('click', () => {
      inputArchive.click();
    });

    inputArchive.style.display = 'none';

    inputArchive.addEventListener('change', (event) => {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const img = new Image();
          img.src = e.target.result;

          img.onload = function () {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const cropWidth = 300;
            const cropHeight = 300;
            canvas.width = cropWidth;
            canvas.height = cropHeight;
            const scaleX = img.width / cropWidth;
            const scaleY = img.height / cropHeight;
            const cropSize = Math.min(scaleX, scaleY);
            const cropX = (img.width - cropWidth * cropSize) / 2;
            const cropY = (img.height - cropHeight * cropSize) / 2;
            ctx.drawImage(
              img,
              cropX, cropY,
              cropWidth * cropSize, cropHeight * cropSize,
              0, 0,
              cropWidth, cropHeight
            );
            selectedImg.src = canvas.toDataURL('image/jpeg');
          };
        };
        reader.readAsDataURL(file);
      }
    });
  }
}
document.addEventListener('DOMContentLoaded', MostrarImagenSeleccionada);
