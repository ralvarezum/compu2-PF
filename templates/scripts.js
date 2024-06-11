document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });
});

var socket = io();

// Manejar la recepción de archivos nuevos
socket.on('file_uploaded', function(data) {
    const fileList = document.getElementById('fileList');
    const li = document.createElement('li');

    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info';
    fileInfo.innerHTML = `<strong>${data.filename}</strong>`;

    const link = document.createElement('a');
    link.href = `/uploads/${data.filename}`;
    link.className = 'download-link';
    link.textContent = ' Descargar';
    fileInfo.appendChild(link);

    li.appendChild(fileInfo);

    const fileMetadata = document.createElement('div');
    fileMetadata.className = 'file-metadata';
    const uploadDate = new Date(data.timestamp * 1000);
    fileMetadata.innerHTML = `Subido por: ${data.uploader} el ${uploadDate.toLocaleString()}`;
    li.appendChild(fileMetadata);

    fileList.appendChild(li);
});

function loadFiles() {
    fetch('/files')
        .then(response => response.json())
        .then(files => {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            for (const [filename, metadata] of Object.entries(files)) {
                const li = document.createElement('li');
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.innerHTML = `<strong>${filename}</strong>`;

                const link = document.createElement('a');
                link.href = `/uploads/${filename}`;
                link.className = 'download-link';
                link.textContent = ' Descargar';
                fileInfo.appendChild(link);

                li.appendChild(fileInfo);

                const fileMetadata = document.createElement('div');
                fileMetadata.className = 'file-metadata';
                const uploadDate = new Date(metadata.timestamp * 1000);
                fileMetadata.innerHTML = `Subido por: ${metadata.uploader} el ${uploadDate.toLocaleString()}`;
                li.appendChild(fileMetadata);

                fileList.appendChild(li);
            }
        });
}

document.addEventListener('DOMContentLoaded', loadFiles);
