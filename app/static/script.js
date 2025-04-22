let websocket = null;

async function convertToMp3() {
    const url = document.getElementById('youtubeUrl').value;
    const convertButton = document.getElementById('convertButton');
    const loading = document.getElementById('loading');
    const downloadLink = document.getElementById('downloadLink');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressContainer = document.getElementById('progress-container');

    if (!url) {
        alert('Por favor, cole um link do YouTube.');
        return;
    }

    progressContainer.style.display = 'block';
    convertButton.disabled = true;
    progressBar.style.width = '0%';
    progressText.textContent = 'Iniciando...';

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

        const file_name = data.file_name;
        const encodeFileName = encodeURIComponent(file_name);

        const fileUrl = `http://localhost:8000/download/${encodeFileName}`;
        console.log("Link de download gerado:", fileUrl);
        downloadLink.innerHTML = `
            <a href="${fileUrl}" class="btn btn-success" download>
                Baixar MP3
            </a>
        `;
    } catch (error) {
        alert(error.message);
    } finally {
        convertButton.disabled = false;
    }
}
