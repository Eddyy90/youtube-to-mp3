async function convertToMp3() {
    const url = document.getElementById('youtubeUrl').value;
    const convertButton = document.getElementById('convertButton');
    const loading = document.getElementById('loading');
    const downloadLink = document.getElementById('downloadLink');

    if (!url) {
        alert('Por favor, cole um link do YouTube.');
        return;
    }

    loading.style.display = 'block';
    convertButton.disabled = true;

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
            <a href="http://localhost:8000/download/${encodeFileName}" class="btn btn-success" download>
                Baixar MP3
            </a>
        `;
    } catch (error) {
        alert(error.message);
    } finally {
        loading.style.display = 'none';
        convertButton.disabled = false;
    }
}

