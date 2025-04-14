// Service Worker 등록
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('ServiceWorker registration successful');
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

let video = document.getElementById('video');
let canvas = document.createElement('canvas');
let preview = document.getElementById('preview');
let startButton = document.getElementById('startCamera');
let captureButton = document.getElementById('capture');
let processButton = document.getElementById('process');
let stream = null;

// 카메라 시작
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment'
            }
        });
        video.srcObject = stream;
        video.play();
        startButton.disabled = true;
        captureButton.disabled = false;
    } catch (err) {
        console.error('카메라 접근 오류:', err);
        alert('카메라 접근 권한이 필요합니다.');
    }
}

// 사진 촬영
function captureImage() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    preview.src = canvas.toDataURL('image/jpeg');
    preview.style.display = 'block';
    video.style.display = 'none';
    
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    
    startButton.disabled = false;
    captureButton.disabled = true;
    processButton.disabled = false;
}

// 문서 처리
async function processDocument() {
    const loading = document.querySelector('.loading');
    loading.style.display = 'block';
    processButton.disabled = true;
    
    try {
        // 이미지 데이터 준비
        const imageData = canvas.toDataURL('image/jpeg').split(',')[1];
        const category = document.getElementById('category').value;
        
        // 서버로 전송
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageData,
                category: category
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // 결과 표시
        document.getElementById('result').textContent = result.text;
        
        // 문서 목록 업데이트
        updateDocumentList();
        
    } catch (err) {
        console.error('처리 오류:', err);
        alert('문서 처리 중 오류가 발생했습니다.');
    } finally {
        loading.style.display = 'none';
        processButton.disabled = false;
    }
}

// 문서 목록 업데이트
async function updateDocumentList() {
    try {
        const response = await fetch('/documents');
        const documents = await response.json();
        
        const list = document.getElementById('documentList');
        list.innerHTML = '';
        
        documents.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'document-item';
            item.innerHTML = `
                <h3>${doc.category}</h3>
                <p>${doc.text.substring(0, 100)}...</p>
                <small>${new Date(doc.created_at).toLocaleString()}</small>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        console.error('문서 목록 업데이트 오류:', err);
    }
}

// 카테고리 목록 로드
async function loadCategories() {
    try {
        const response = await fetch('/categories');
        const categories = await response.json();
        
        const select = document.getElementById('category');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('카테고리 로드 오류:', err);
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    updateDocumentList();
    
    startButton.addEventListener('click', startCamera);
    captureButton.addEventListener('click', captureImage);
    processButton.addEventListener('click', processDocument);
}); 