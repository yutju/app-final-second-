# templates.py

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SixSense Doc-Converter | 프리미엄 문서 PDF 변환 서비스</title>

    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">

    <style>
        :root {
            --primary: #4F46E5;
            --primary-dark: #4338CA;
            --bg-main: #F9FAFB;
            --text-main: #1F2937;
            --glass-bg: rgba(255, 255, 255, 0.8);
            --glass-border: rgba(255, 255, 255, 0.2);
        }

        body { font-family: 'Noto Sans KR', sans-serif; background-color: var(--bg-main); color: var(--text-main); scroll-behavior: smooth; }
        .font-poppins { font-family: 'Poppins', sans-serif; }

        .gradient-bg {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

        .glass-card { background: var(--glass-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--glass-border); }
        .hover-lift { transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .hover-lift:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }

        .drop-zone { border: 3px dashed #d1d5db; transition: all 0.3s ease; cursor: pointer; }
        .drop-zone.active { border-color: var(--primary); background-color: #EEF2FF; }

        .title-underline { width: 60px; height: 5px; background: #6366F1; margin: 15px auto 0; border-radius: 10px; }
        .infra-card { background: #312E81; color: #E0E7FF; border-radius: 2rem; padding: 3rem; }
        .api-box { background: #111827; color: #A5B4FC; border-radius: 2rem; padding: 3rem; font-family: 'Courier New', monospace; position: relative; overflow: hidden; }
        .api-label { position: absolute; top: 1.5rem; right: 2rem; font-size: 4rem; font-weight: 900; color: rgba(255,255,255,0.03); font-family: 'Poppins', sans-serif; }
        .code-comment { color: #6B7280; }
        .code-method { color: #C4B5FD; }
        .code-path { color: #34D399; }

        .loader-ring { display: inline-block; width: 80px; height: 80px; position: relative; }
        .loader-ring div { box-sizing: border-box; display: block; position: absolute; width: 64px; height: 64px; margin: 8px; border: 8px solid var(--primary); border-radius: 50%; animation: loader-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite; border-color: var(--primary) transparent transparent transparent; }
        @keyframes loader-ring { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="min-h-screen">

    <nav class="glass-card sticky top-0 z-50 border-b shadow-sm">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-2">
                <span class="text-3xl">👀</span>
                <span class="text-3xl font-extrabold tracking-tighter text-gray-900 font-poppins">SixSense</span>
            </div>
            <div class="flex items-center space-x-8 text-sm font-bold text-gray-600">
                <a href="#about" class="hover:text-indigo-600 transition">서비스 소개</a>
                <a href="#formats" class="hover:text-indigo-600 transition">지원 형식</a>
                <a href="#api" class="hover:text-indigo-600 transition">API 문서</a>
                <button class="bg-indigo-600 text-white px-6 py-2.5 rounded-full hover:bg-indigo-700 transition shadow-lg">프리미엄 가입</button>
            </div>
        </div>
    </nav>

    <header class="gradient-bg py-24 text-white text-center">
        <div class="max-w-5xl mx-auto px-6">
            <h1 class="text-6xl font-black tracking-tight leading-tight font-poppins mb-6">단 한 번의 드래그로,<br>모든 문서를 <span class="text-yellow-300">완벽한 PDF</span>로</h1>
            <p class="text-xl font-light opacity-90">인프라 엔지니어를 위한 초고속 프리미엄 변환 서비스</p>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 -mt-20 space-y-20 pb-32 relative z-10">

        <div id="formats" class="glass-card p-12 rounded-3xl shadow-2xl hover-lift">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 items-center">
                <div class="md:col-span-1 pr-6 border-r border-gray-100">
                    <h2 class="text-3xl font-black text-gray-900 mb-6">스마트 업로드</h2>
                    <p class="text-gray-600 mb-8 leading-relaxed">PNG, JPG, DOCX, HWP, TXT 파일을 지원합니다. (최대 100MB)</p>
                    <div class="space-y-4">
                        <div class="flex items-center space-x-3 text-sm text-green-700 font-bold bg-green-50 p-4 rounded-xl border border-green-100">✅ 나눔고딕 폰트 한글 완벽 지원</div>
                        <div class="flex items-center space-x-3 text-sm text-indigo-700 font-bold bg-indigo-50 p-4 rounded-xl border border-indigo-100">✅ 인프라 팀 전용 하이브리드 엔진</div>
                    </div>
                </div>
                <div class="md:col-span-2">
                    <form id="uploadForm" class="space-y-8">
                        <div id="dropZone" class="drop-zone p-16 text-center rounded-3xl bg-gray-50 hover:bg-white transition shadow-inner">
                            <div class="text-6xl mb-6">📄</div>
                            <p class="text-2xl font-black text-gray-800">파일을 드래그하거나 클릭하세요</p>
                            <input type="file" id="fileInput" name="file" class="hidden" required>
                        </div>
                        <div id="fileInfo" class="hidden bg-indigo-50 p-6 rounded-2xl border border-indigo-200 flex justify-between items-center shadow-sm">
                            <div class="flex items-center space-x-4">
                                <span class="text-2xl">📎</span>
                                <span id="fileName" class="text-indigo-900 font-black text-lg"></span>
                            </div>
                            <button type="button" id="removeFile" class="text-red-500 text-2xl font-bold">❌</button>
                        </div>
                        <button type="submit" class="w-full bg-indigo-600 text-white font-black py-6 rounded-2xl text-2xl shadow-xl hover:bg-indigo-700 transition transform hover:-translate-y-1">PDF 변환 시작 ✨</button>
                    </form>
                </div>
            </div>
        </div>

        <section id="about" class="bg-white p-16 rounded-3xl shadow-xl border border-gray-100">
            <div class="text-center mb-16">
                <h2 class="text-5xl font-black text-gray-900 font-poppins">About SixSense</h2>
                <div class="title-underline"></div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-5 gap-16 items-center">
                <div class="md:col-span-3 text-gray-700 text-xl leading-relaxed space-y-6 font-medium">
                    <p>SixSense는 복잡한 문서 변환 과정을 단 한 번의 드래그로 해결하기 위해 탄생했습니다. 인프라 엔지니어의 시각에서 <span class="text-indigo-600 font-black">보안</span>과 <span class="text-indigo-600 font-black">성능</span>을 최우선으로 설계되었습니다.</p>
                    <p>우리는 오픈소스 엔진인 LibreOffice와 Pillow를 최적화하여 어떤 환경에서도 깨짐 없는 완벽한 PDF 결과물을 보장합니다. 특히 K3s 기반의 클라우드 네이티브 환경에서 중단 없는 서비스를 제공합니다.</p>
                </div>
                <div class="md:col-span-2">
                    <div class="infra-card shadow-2xl">
                        <h3 class="text-2xl font-black mb-8 font-poppins text-white border-b border-indigo-400 pb-4">Core Infrastructure</h3>
                        <ul class="space-y-5 text-lg font-bold">
                            <li class="flex items-center text-indigo-100"><span class="mr-3 text-indigo-400">•</span> Containerized with Docker</li>
                            <li class="flex items-center text-indigo-100"><span class="mr-3 text-indigo-400">•</span> Orchestrated by K3s</li>
                            <li class="flex items-center text-indigo-100"><span class="mr-3 text-indigo-400">•</span> Automated with Ansible & Terraform</li>
                            <li class="flex items-center text-indigo-100"><span class="mr-3 text-indigo-400">•</span> Monitored by Prometheus & Grafana</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <section id="api" class="space-y-12">
            <div class="text-center">
                <h2 class="text-5xl font-black text-gray-900 font-poppins">Developer API</h2>
                <div class="title-underline"></div>
            </div>
            <div class="api-box shadow-2xl">
                <div class="api-label">API</div>
                <div class="space-y-8 text-lg">
                    <div>
                        <p class="code-comment mb-3 font-bold">// POST request to convert any file</p>
                        <p class="font-black text-2xl tracking-tight">
                            <span class="code-method">POST</span>
                            <span class="code-path">/convert-to-pdf/</span>
                        </p>
                    </div>
                    <div>
                        <p class="text-indigo-300 font-bold mb-3 underline">Header</p>
                        <p class="text-gray-300">Content-Type: <span class="text-white">multipart/form-data</span></p>
                    </div>
                    <div class="pl-6 border-l-4 border-gray-700 py-2">
                        <p class="code-comment mb-3"># Request Body</p>
                        <p class="text-xl font-bold"><span class="text-indigo-400">file:</span> <span class="text-white">your_document.hwp</span></p>
                    </div>
                    <div class="pt-6 border-t border-gray-800">
                        <p class="code-comment mb-3">// Check system health</p>
                        <p class="font-black text-xl">
                            <span class="code-method">GET</span>
                            <span class="code-path">/health</span>
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <p class="text-center text-gray-400 font-bold mt-12">© 2026 SixSense Project | Built with ❤ for Infrastructure Engineers</p>
    </main>

    <div id="loadingScreen" class="hidden fixed inset-0 bg-gray-900 bg-opacity-80 flex items-center justify-center z-50 backdrop-blur-md">
        <div class="bg-white p-16 rounded-3xl text-center shadow-2xl">
            <div class="loader-ring mx-auto mb-8"><div></div></div>
            <p class="text-3xl font-black text-gray-900 animate-pulse">엔진 가동 중...</p>
        </div>
    </div>

    <div id="resultArea" class="hidden fixed inset-0 bg-gray-900 bg-opacity-90 flex items-center justify-center z-50 backdrop-blur-xl transition-all duration-500 opacity-0 transform scale-95">
        <div class="bg-white p-24 rounded-3xl text-center shadow-2xl border-4 border-green-500 max-w-2xl w-full mx-6">
            <span class="text-9xl">🎉</span>
            <h2 class="text-7xl font-black text-green-800 mt-10 tracking-tighter leading-none">변환 성공!</h2>
            <p class="text-green-700 mt-6 text-2xl font-bold">프리미엄 PDF 문서를 지금 확인하세요.</p>
            <a id="downloadLink" href="#" class="inline-block mt-16 gradient-bg text-white font-black p-8 w-full rounded-2xl text-4xl shadow-2xl hover:opacity-95 transition transform hover:-translate-y-2" download>📥 다운로드</a>
            <button onclick="document.getElementById('resultArea').classList.add('hidden')" class="mt-10 text-gray-400 hover:text-gray-600 text-lg font-bold underline">창 닫기</button>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script>
        const uploadForm = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const dropZone = document.getElementById('dropZone');
        const fileInfo = document.getElementById('fileInfo');
        const fileNameDisp = document.getElementById('fileName');
        const removeFileBtn = document.getElementById('removeFile'); // [수정] 버튼 변수 추가
        const loadingScreen = document.getElementById('loadingScreen');
        const resultArea = document.getElementById('resultArea');
        const downloadLink = document.getElementById('downloadLink');

        dropZone.onclick = () => fileInput.click();
        
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if(file) {
                fileNameDisp.textContent = file.name;
                fileInfo.classList.remove('hidden');
                resultArea.classList.add('hidden');
            }
        };

        // [추가] X 버튼 클릭 이벤트: 파일 초기화 로직
        removeFileBtn.onclick = (e) => {
            e.stopPropagation(); // 부모(dropZone) 클릭 이벤트 방지
            fileInput.value = ''; // 실제 input 파일 데이터 비우기
            fileInfo.classList.add('hidden'); // 화면에서 파일 정보 숨기기
            resultArea.classList.add('hidden'); // 변환 결과 숨기기
        };

        uploadForm.onsubmit = async (e) => {
            e.preventDefault();
            const file = fileInput.files[0];
            if(!file) return;
            const formData = new FormData();
            formData.append('file', file);
            loadingScreen.classList.remove('hidden');
            try {
                const res = await axios.post('/convert-to-pdf/', formData, { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data]));
                downloadLink.href = url;
                downloadLink.download = file.name.split('.')[0] + ".pdf";
                resultArea.classList.remove('hidden');
                setTimeout(() => { resultArea.classList.remove('opacity-0', 'scale-95'); }, 10);
            } catch (err) { alert('변환 실패!'); }
            finally { loadingScreen.classList.add('hidden'); }
        };
    </script>
</body>
</html>
"""
