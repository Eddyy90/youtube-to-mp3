let websocket = null;

async function convertToMp3() {
    const url = document.getElementById('youtubeUrl').value;
    const convertButton = document.getElementById('convertButton');
    const loading = document.getElementById('loading');
    const downloadLink = document.getElementById('downloadLink');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressContainer = document.getElementById('progress-container');
    const downloadListContainer = document.querySelector('.downloadlist');

    if (!url) {
        alert('Por favor, cole um link do YouTube.');
        return;
    }

    progressContainer.style.display = 'block';
    convertButton.disabled = true;
    progressBar.style.width = '0%';
    progressText.textContent = 'Iniciando...';
    downloadListContainer.innerHTML = '';
    downloadLink.innerHTML = '';

    let progressInterval = setInterval(async () => {
        try {
            const response = await fetch('http://localhost:8000/progress');
            const data = await response.json();

            if (data.percent >= 0) {
                progressBar.style.width = data.percent + '%';
                progressText.textContent = `Progresso: ${Math.round(data.percent)}%`;

                if (data.percent === 100) {
                    clearInterval(progressInterval);
                }
            }
        } catch (error) {
            console.error('Erro ao buscar progresso:', error);
        }
    }, 200);

    try {
        const response = await fetch(`http://localhost:8000/convert/?url=${encodeURIComponent(url)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Erro ao converter o vídeo.');
        }

        const data = await response.json();
        const files = data.files || [];
        const zipFile = data.zip_file;

        if (files.length > 0) {
            files.forEach(file => {
                const fileUrl = `http://localhost:8000/download/${encodeURIComponent(file)}`;
                const fileLink = document.createElement('a');
                fileLink.href = fileUrl;
                fileLink.textContent = `🎵 ${file}`;
                fileLink.className = 'list-group-item list-group-item-action';
                fileLink.download = file;
                downloadListContainer.appendChild(fileLink);
                downloadListContainer.appendChild(document.createElement('br'));
            });

            if (zipFile) {
                const zipUrl = `http://localhost:8000/download/${encodeURIComponent(zipFile)}`;
                downloadLink.innerHTML = `
                    <a href="${zipUrl}" class="btn btn-success mt-3" download>
                        📦 Baixar Playlist Inteira (ZIP)
                    </a>
                `;
            }
        } else {
            downloadLink.innerHTML = `<div class="alert alert-warning">Nenhum arquivo encontrado!</div>`;
        }

    } catch (error) {
        alert(error.message);
    } finally {
        convertButton.disabled = false;
    }
}

async function loadDownloadList() {
    const downloadListDiv = document.querySelector('.downloadlist');
    downloadListDiv.innerHTML = '';

    try {
        const response = await fetch('http://localhost:8000/list-downloads');
        const data = await response.json();

        if (data.files.length === 0) {
            downloadListDiv.innerHTML = '<p class="text-center">Nenhum arquivo disponível.</p>';
            return;
        }

        const listGroup = document.createElement('div');
        listGroup.className = 'list-group';

        data.files.forEach(fileName => {
            const encodedFileName = encodeURIComponent(fileName);
            const fileUrl = `http://localhost:8000/download/${encodedFileName}`;

            const item = document.createElement('a');
            item.href = fileUrl;
            item.className = 'list-group-item list-group-item-action';
            item.download = fileName;
            item.textContent = fileName;

            listGroup.appendChild(item);
        });

        downloadListDiv.appendChild(listGroup);

    } catch (error) {
        console.error('Erro ao carregar a lista de downloads:', error);
    }
}

loadDownloadList();