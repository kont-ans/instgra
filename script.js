document.addEventListener('DOMContentLoaded', () => {
    const introOverlay = document.getElementById('intro-overlay');
    const mainWrapper = document.querySelector('.main-wrapper');
    const sidebar = document.getElementById('sidebar');
    const openSidebar = document.getElementById('open-sidebar');
    const closeSidebar = document.getElementById('close-sidebar');
    const videoUrlInput = document.getElementById('video-url');
    const downloadBtn = document.getElementById('download-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const resultsContainer = document.getElementById('results-container');
    const videoTitle = document.getElementById('video-title');
    const videoLinksList = document.getElementById('video-links');
    const audioLinksList = document.getElementById('audio-links');
    const showVideoOptions = document.getElementById('show-video-options');
    const showAudioOptions = document.getElementById('show-audio-options');
    const videoOptions = document.getElementById('video-options');
    const audioOptions = document.getElementById('audio-options');

    // 1. Hero Animation
    setTimeout(() => {
        introOverlay.style.opacity = '0';
        introOverlay.style.transform = 'scale(1.1)';
        mainWrapper.classList.remove('hidden-initially');
        mainWrapper.classList.add('visible');
        setTimeout(() => { introOverlay.style.display = 'none'; }, 1000);
    }, 2000);

    // 2. Sidebar Logic
    openSidebar.addEventListener('click', () => sidebar.classList.add('active'));
    closeSidebar.addEventListener('click', () => sidebar.classList.remove('active'));

    // 3. Download Logic
    downloadBtn.addEventListener('click', async () => {
        const url = videoUrlInput.value.trim();
        if (!url) { alert('يرجى إدخال رابط صالح أولاً!'); return; }

        setLoading(true);
        resultsContainer.classList.add('hidden');
        videoOptions.classList.add('hidden');
        audioOptions.classList.add('hidden');

        try {
            const response = await fetch(`api-bridge.php?url=${encodeURIComponent(url)}`);
            if (!response.ok) throw new Error('فشل الاتصال بالخادم');
            const data = await response.json();

            if (data && data.links && data.links.length > 0) {
                displayResults(data);
            } else {
                alert(data.error || 'لم يتم العثور على روابط تحميل. تأكد من صحة الرابط.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('حدث خطأ أثناء جلب البيانات. يرجى المحاولة لاحقاً.');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
            downloadBtn.disabled = true;
        } else {
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
            downloadBtn.disabled = false;
        }
    }

    function displayResults(data) {
        videoTitle.textContent = data.title || 'تم العثور على المحتوى';
        videoLinksList.innerHTML = '';
        audioLinksList.innerHTML = '';

        data.links.forEach(link => {
            const item = createDownloadItem(link, data.title);
            if (link.type.includes('video')) {
                videoLinksList.appendChild(item);
            } else if (link.type.includes('audio')) {
                audioLinksList.appendChild(item);
            }
        });

        resultsContainer.classList.remove('hidden');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function createDownloadItem(link, title) {
        const div = document.createElement('div');
        div.className = 'download-item';
        div.textContent = link.quality;
        
        div.addEventListener('click', (e) => {
            e.preventDefault();
            // استخدام اسم ثابت للموقع مع اللاحقة الصحيحة الممررة من الـ API
            const typeLabel = link.type.includes('video') ? 'Video' : 'Audio';
            const fixedFilename = `Ultra_Download_${typeLabel}`;
            initiateDownload(link.url, fixedFilename, link.ext);
        });

        return div;
    }

    // 4. Toggle Options
    showVideoOptions.addEventListener('click', () => {
        videoOptions.classList.toggle('hidden');
        audioOptions.classList.add('hidden');
    });

    showAudioOptions.addEventListener('click', () => {
        audioOptions.classList.toggle('hidden');
        videoOptions.classList.add('hidden');
    });

    // 5. Direct Download via Proxy
    function initiateDownload(url, filename, ext) {
        const originalTitle = videoTitle.textContent;
        videoTitle.textContent = 'جاري بدء التحميل...';
        
        // تمرير اللاحقة (ext) لضمان إضافتها في الجسر البرمجي
        const proxyUrl = `api-bridge.php?download_url=${encodeURIComponent(url)}&filename=${encodeURIComponent(filename)}&ext=${encodeURIComponent(ext)}`;
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = proxyUrl;
        a.download = `${filename}.${ext}`; // محاولة إضافية للمتصفح
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
            document.body.removeChild(a);
            videoTitle.textContent = originalTitle;
        }, 2000);
    }
});
