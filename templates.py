
from components import ABOUT_SECTION, API_SECTION

# 상단 UI 및 내비게이션 바
HTML_HEADER = """
<!DOCTYPE html>
<html lang="ko" style="scroll-behavior: smooth;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SixSense Doc-Converter | 프리미엄 변환 & 보안 서비스</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js"></script>
    <style>
        :root { --primary: #4F46E5; --primary-dark: #4338CA; --bg-main: #F9FAFB; --text-main: #1F2937; --glass-bg: rgba(255, 255, 255, 0.9); }
        body { font-family: 'Noto Sans KR', sans-serif; background-color: var(--bg-main); color: var(--text-main); }
        .font-poppins { font-family: 'Poppins', sans-serif; }
        .gradient-bg { background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab); background-size: 400% 400%; animation: gradient 15s ease infinite; }
        @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .glass-card { background: var(--glass-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.2); }
        .drop-zone { border: 3px dashed #d1d5db; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; min-height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; border-radius: 1.5rem; }
        .drop-zone.active { border-color: var(--primary); background-color: #EEF2FF; transform: scale(1.02); }
        .tab-btn { transition: all 0.3s ease; border-radius: 9999px; font-weight: 800; padding: 0.75rem 2.5rem; }
        .tab-btn.active { background-color: var(--primary); color: white; box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4); }
        .tab-btn.inactive { background-color: #E5E7EB; color: #6B7280; }
        .sortable-ghost { opacity: 0.4; background: #EEF2FF !important; border: 2px dashed var(--primary) !important; }

        .icon-pop { animation: success-pop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        @keyframes success-pop { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.05); } 100% { transform: scale(1); opacity: 1; } }
        @keyframes slow-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin-slow { animation: slow-spin 3s linear infinite; }
        .icon-mega-scale { width: 36rem !important; height: auto; }

        /* 🔒 토글 스위치 스타일 */
        .toggle-dot { transition: all 0.3s ease-in-out; }
        input:checked ~ .toggle-dot { transform: translateX(100%); background-color: #4F46E5; }
        input:checked ~ .toggle-bg { background-color: #E0E7FF; }

        /* 📄 A4 비율 미리보기 스타일 */
        .preview-wrapper { display: flex; flex-direction: column; align-items: center; background: #f3f4f6; padding: 2rem; border-radius: 1.5rem; margin-top: 1rem; border: 1px solid #e5e7eb; }
        .a4-page { background: white; width: 280px; height: 396px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); position: relative; overflow: hidden; border-radius: 2px; }
        canvas { width: 100%; height: 100%; }

        .loader-ring { display: inline-block; width: 80px; height: 80px; position: relative; }
        .loader-ring div { box-sizing: border-box; display: block; position: absolute; width: 64px; height: 64px; margin: 8px; border: 8px solid var(--primary); border-radius: 50%; animation: loader-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite; border-color: var(--primary) transparent transparent transparent; }
        @keyframes loader-ring { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* ✨ 용량 게이지 바 공통 애니메이션 */
        .gauge-container { width: 100%; max-width: 400px; height: 8px; background: #e5e7eb; border-radius: 9999px; overflow: hidden; margin: 10px 0; }
        .size-gauge-bar { height: 100%; width: 0%; background: var(--primary); transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s; }
        .gauge-warning { background: #EF4444 !important; }

        /* 드롭존 업로드 애니메이션 아이콘 */
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .animate-float { animation: float 2s ease-in-out infinite; }

        /* 🔔 [신규] 토스트 메시지 스타일 */
        #toastContainer { position: fixed; bottom: 30px; right: 30px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
        .toast { padding: 16px 24px; border-radius: 16px; color: white; font-weight: 800; font-size: 14px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2); transform: translateX(120%); transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55); display: flex; items-center: center; space-x: 3: }
        .toast.show { transform: translateX(0); }
        .toast-success { background: #10B981; }
        .toast-error { background: #EF4444; }
        .toast-info { background: #4F46E5; }
    </style>
</head>
<body class="min-h-screen">
    <div id="toastContainer"></div>

    <nav class="glass-card sticky top-0 z-50 border-b shadow-sm">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <img src="/static/sixsenselogo.png" alt="SixSense Logo" class="h-10 w-auto object-contain rounded-lg">
                <span class="text-3xl font-extrabold tracking-tighter text-gray-900 font-poppins">SixSense</span>
            </div>
            <div class="flex items-center space-x-8 text-sm font-bold text-gray-600">
                <a href="#convert" class="hover:text-indigo-600 transition">변환하기</a>
                <a href="#about" class="hover:text-indigo-600 transition">서비스 소개</a>
                <a href="#api" class="hover:text-indigo-600 transition">API 문서</a>
                <button class="bg-indigo-600 text-white px-6 py-2.5 rounded-full shadow-lg font-bold">Cloud Native</button>
            </div>
        </div>
    </nav>

    <header class="gradient-bg py-24 text-white text-center">
        <div class="max-w-5xl mx-auto px-6">
            <h1 class="text-6xl font-black tracking-tight leading-tight font-poppins mb-6">단 한 번의 드래그로,<br>모든 문서를 <span class="text-yellow-300">완벽한 PDF</span>로</h1>
            <p class="text-xl font-light opacity-90"> IT 엔지니어를 위한 듀얼 엔진 PDF 통합 변환 서비스</p>
        </div>
    </header>

    <main id="convert" class="max-w-7xl mx-auto px-6 -mt-20 space-y-20 pb-32 relative z-10">
        <div class="glass-card p-12 rounded-3xl shadow-2xl">
            <div class="flex justify-center space-x-4 mb-10 bg-gray-100 p-2 rounded-full w-max mx-auto">
                <button id="btnSingle" class="tab-btn active">단일 파일 변환</button>
                <button id="btnMerge" class="tab-btn inactive">다중 파일 병합</button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 items-start">
                <div class="md:col-span-1 pr-6 border-r border-gray-100 sticky top-32">
                    <h2 id="guideTitle" class="text-3xl font-black text-gray-900 mb-6 font-poppins tracking-tighter">Smart Upload</h2>
                    <p id="guideDesc" class="text-gray-600 mb-8 leading-relaxed font-bold text-sm">PNG, JPG, JPEG, BMP, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT 지원 (최대 50MB)</p>

                    <div class="bg-gray-50 p-6 rounded-2xl border border-gray-200 space-y-4 shadow-sm mb-4">
                        <h3 class="font-black text-indigo-900 flex items-center text-sm">🎨 워터마크 디자인</h3>
                        <select id="wmType" class="w-full p-3 rounded-xl border-2 border-gray-200 font-bold text-sm focus:border-indigo-500 outline-none">
                            <option value="none">❌ 워터마크 적용 안 함</option>
                            <option value="text">🔠 텍스트 워터마크</option>
                            <option value="image">🖼️ 로고 이미지</option>
                        </select>
                        <div id="wmTextGroup" class="hidden">
                            <input type="text" id="wmText" placeholder="워터마크 문구 입력" class="w-full p-3 rounded-xl border-2 border-gray-200 font-bold text-sm">
                        </div>
                        <div id="wmImageGroup" class="hidden">
                            <input type="file" id="wmImage" accept="image/*" class="w-full text-xs font-bold text-gray-400">
                        </div>

                        <div id="wmAdvanced" class="hidden space-y-3 pt-2 border-t border-gray-100">
                            <div>
                                <label class="text-xs font-black text-gray-500 uppercase tracking-widest">위치</label>
                                <select id="wmPosition" class="w-full mt-1 p-2.5 rounded-xl border-2 border-gray-200 font-bold text-sm">
                                    <option value="center">⊙ 중앙</option>
                                    <option value="top-left">↖ 좌상단</option>
                                    <option value="top-right">↗ 우상단</option>
                                    <option value="bottom-left">↙ 좌하단</option>
                                    <option value="bottom-right">↘ 우하단</option>
                                </select>
                            </div>
                            <div>
                                <div class="flex justify-between items-center text-xs font-black text-gray-500">
                                    <span>크기</span><span id="wmSizeVal" class="text-indigo-600">60</span>
                                </div>
                                <input type="range" id="wmSize" min="10" max="250" value="60" class="w-full mt-1 accent-indigo-600">
                            </div>
                            <div>
                                <div class="flex justify-between items-center text-xs font-black text-gray-500">
                                    <span>투명도</span><span id="wmOpacityVal" class="text-indigo-600">30%</span>
                                </div>
                                <input type="range" id="wmOpacity" min="5" max="100" value="30" class="w-full mt-1 accent-indigo-600">
                            </div>
                            <div>
                                <div class="flex justify-between items-center text-xs font-black text-gray-500">
                                    <span>회전</span><span id="wmRotationVal" class="text-indigo-600">45°</span>
                                </div>
                                <input type="range" id="wmRotation" min="0" max="360" value="45" class="w-full mt-1 accent-indigo-600">
                            </div>
                        </div>
                    </div>

                    <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm mb-4">
                        <div class="flex items-center justify-between">
                            <h3 class="font-black text-indigo-900 flex items-center text-sm">🔢 페이지 번호 삽입</h3>
                            <label class="flex items-center cursor-pointer">
                                <div class="relative">
                                    <input type="checkbox" id="usePageNumber" class="sr-only" onchange="drawWmPreview()">
                                    <div class="toggle-bg block bg-gray-200 w-10 h-6 rounded-full transition"></div>
                                    <div class="toggle-dot absolute left-0.5 top-0.5 bg-white w-4 h-4 rounded-full transition shadow-sm border border-gray-100"></div>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="bg-indigo-50 p-6 rounded-2xl border border-indigo-100 space-y-4 shadow-sm mb-8">
                        <div class="flex items-center justify-between">
                            <h3 class="font-black text-indigo-900 flex items-center text-sm">🔐 PDF 비밀번호 잠금</h3>
                            <label class="flex items-center cursor-pointer">
                                <div class="relative">
                                    <input type="checkbox" id="useEncryption" class="sr-only" onchange="toggleEncryption()">
                                    <div class="toggle-bg block bg-gray-200 w-10 h-6 rounded-full transition"></div>
                                    <div class="toggle-dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition shadow-sm"></div>
                                </div>
                                <span class="ml-3 text-xs font-bold text-gray-600" id="encryptStatusText">사용 안 함</span>
                            </label>
                        </div>
                        <div id="encryptionGroup" class="hidden">
                            <input type="password" id="pdfPassword" placeholder="열기 비밀번호 설정" class="w-full p-3 rounded-xl border-2 border-white font-bold text-sm outline-none">
                        </div>
                    </div>

                    <div class="space-y-4">
                        <div class="flex items-center space-x-3 text-sm text-green-700 font-bold bg-green-50 p-4 rounded-xl border border-green-100">✅ 나눔고딕 & Office 완벽 지원</div>
                        <div class="flex items-center space-x-3 text-sm text-indigo-700 font-bold bg-indigo-50 p-4 rounded-xl border border-indigo-100">✅ S3 보안 스토리지 연동</div>
                    </div>
                </div>

                <div class="md:col-span-2">
                    <div id="sectionSingle" class="space-y-6">
                        <div id="dropZoneSingle" class="drop-zone bg-gray-50 hover:bg-white shadow-inner p-10">
                            <div class="text-7xl mb-4 animate-float">📄</div>
                            <p class="text-2xl font-black text-gray-800">단일 파일을 클릭 및 드래그로 업로드하세요.</p>

                            <div id="singleGaugeWrapper" class="hidden w-full flex flex-col items-center mt-4">
                                <div class="gauge-container"><div id="singleSizeBar" class="size-gauge-bar"></div></div>
                                <p id="singleGaugeLabel" class="text-xs font-bold text-indigo-600">0.0 MB / 50 MB</p>
                            </div>

                            <input type="file" id="inputSingle" class="hidden">
                        </div>
                        <div id="infoSingle" class="hidden bg-white p-6 rounded-2xl border-2 border-indigo-100 flex justify-between items-center shadow-lg">
                            <div class="truncate">
                                <span id="nameSingle" class="text-indigo-900 font-black text-lg truncate block"></span>
                                <span id="sizeSingle" class="text-indigo-500 text-xs font-black uppercase tracking-widest"></span>
                            </div>
                            <button onclick="resetSingle()" class="bg-red-50 text-red-500 p-2 rounded-full ml-3 hover:bg-red-100 transition">✕</button>
                        </div>
                        <div id="wmPreviewBoxSingle" class="hidden preview-wrapper">
                            <p class="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 text-center">A4 규격 실시간 가이드</p>
                            <div class="a4-page"><canvas id="wmCanvasSingle"></canvas></div>
                        </div>
                        <button onclick="handleSingleUpload()" class="w-full bg-indigo-600 text-white font-black py-6 rounded-2xl text-2xl shadow-xl hover:bg-indigo-700 transition transform hover:-translate-y-1">📄 PDF 단일 변환 시작 ✨</button>
                    </div>

                    <div id="sectionMerge" class="hidden space-y-6">
                        <div id="dropZoneMerge" class="drop-zone bg-gray-50 hover:bg-white shadow-inner p-10">
                            <div class="text-7xl mb-4 animate-float">📑📑</div>
                            <p class="text-2xl font-black text-gray-800">여러 파일을 클릭 및 드래그로 업로드하세요.</p>

                            <div id="gaugeWrapper" class="hidden w-full flex flex-col items-center mt-4">
                                <div class="gauge-container"><div id="sizeGaugeBar" class="size-gauge-bar"></div></div>
                                <p id="gaugeLabel" class="text-xs font-bold text-indigo-600">0.0 MB / 50 MB</p>
                            </div>

                            <p class="text-sm text-gray-400 mt-2 font-bold" id="mergeStatus">현재 0개 선택됨 (총 0MB)</p>
                            <input type="file" id="inputMerge" class="hidden" multiple>
                        </div>
                        <div id="listMerge" class="hidden space-y-3 p-4 border-2 border-indigo-50 rounded-2xl bg-gray-50/50 max-h-60 overflow-y-auto shadow-inner"></div>
                        <div id="wmPreviewBoxMerge" class="hidden preview-wrapper">
                            <p class="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 text-center">병합 문서 통합 가이드</p>
                            <div class="a4-page"><canvas id="wmCanvasMerge"></canvas></div>
                        </div>
                        <p class="text-xs text-center text-indigo-400 font-bold py-2 italic">💡 마우스로 끌어서 파일의 합쳐질 순서를 바꿀 수 있습니다.</p>
                        <button onclick="handleMergeUpload()" class="w-full bg-indigo-600 text-white font-black py-6 rounded-2xl text-2xl shadow-xl hover:bg-indigo-700 transition transform hover:-translate-y-1">📑 통합 PDF 병합 시작 ⚡</button>
                    </div>
                </div>
            </div>
        </div>
"""

HTML_FOOTER = """
        <p class="text-center text-gray-400 font-bold mt-12 font-poppins">© 2026 SixSense Project | Built for Infrastructure Engineers</p>
    </main>

    <div id="loadingScreen" class="hidden fixed inset-0 bg-gray-900 bg-opacity-80 flex items-center justify-center z-50 backdrop-blur-md">
        <div class="bg-white p-12 rounded-3xl text-center shadow-2xl max-w-md w-full mx-6">
            <div class="loader-ring mx-auto mb-8"><div></div></div>
            <div class="space-y-4">
                <div class="flex justify-between items-end mb-1">
                    <p id="loadingStatus" class="text-sm font-black text-indigo-600">엔진 시동 중...</p>
                    <p id="percentText" class="text-2xl font-black text-gray-800 font-poppins">0%</p>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-4 overflow-hidden"><div id="progressBar" class="bg-indigo-600 h-full w-0 transition-all duration-500"></div></div>
                <p id="loadingSubText" class="text-xs text-gray-400 font-bold">인프라 자원을 할당받고 있습니다...</p>
            </div>
        </div>
    </div>

    <div id="resultArea" class="hidden fixed inset-0 bg-gray-900/60 flex items-center justify-center z-50 backdrop-blur-xl transition-all duration-500">
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
            <div class="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-500/15 blur-[120px] animate-pulse"></div>
            <div class="absolute -bottom-[10%] -right-[10%] w-[50%] h-[50%] rounded-full bg-emerald-500/15 blur-[120px] animate-pulse"></div>
        </div>
        <div class="p-16 rounded-[3.5rem] text-center shadow-[0_35px_60px_-15px_rgba(0,0,0,0.3)] border border-white/40 max-w-2xl w-full mx-6 relative z-10 icon-pop"
             style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(50px);">
            <div class="flex justify-center mb-6"><img src="/static/convert.png" alt="Success" class="icon-mega-scale object-contain animate-bounce"></div>
            <h2 class="text-6xl font-black text-gray-900 tracking-tighter mb-4 font-poppins">변환 완료!</h2>
            <p class="text-xl text-gray-600 font-bold mb-8 opacity-90">pdf 파일 변환 및 S3 보관 완료</p>
            <div class="inline-flex items-center space-x-3 px-8 py-3 rounded-full bg-white/50 border border-gray-200 text-gray-700 font-black mb-12 shadow-sm">
                <span class="text-2xl animate-spin-slow">⏱️</span>
                <span id="expiryTimer" class="text-lg tracking-tighter font-poppins">05:00 후 자동 파기</span>
            </div>
            <div class="space-y-5">
                <a id="downloadLink" href="#" download class="flex items-center justify-center bg-indigo-600 text-white font-black p-6 w-full rounded-2xl text-3xl shadow-lg hover:bg-indigo-700 transition transform hover:-translate-y-1 active:scale-95">PDF 다운로드</a>
                <button onclick="copyToClipboard()" id="copyBtn" class="flex items-center justify-center space-x-3 bg-white/80 text-gray-700 font-bold p-5 w-full rounded-2xl border border-gray-200 shadow-sm hover:bg-white transition active:scale-95 text-lg">
                    <span>🔗</span> <span id="copyBtnText">S3 PDF 공유 링크 복사</span>
                </button>
            </div>
            <button onclick="location.reload()" class="mt-12 text-gray-400 hover:text-indigo-600 font-bold underline transition-colors">새 문서 변환하기</button>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script>
        const wmType = document.getElementById('wmType');
        let singleFile = null; let mergeFiles = [];
        let currentTab = 'single'; let wmLogoImg = null;
        let progressInterval = null; let timerInterval = null;
        let currentDownloadUrl = "";

        // 🔔 [신규] 세련된 토스트 메시지 생성 함수
        function showToast(msg, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `<span>${type === 'error' ? '🚨' : (type === 'success' ? '✅' : 'ℹ️')}</span> <span>${msg}</span>`;
            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 100);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }, 10000);
        }

        function formatSize(bytes) {
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function drawWmPreview() {
            const type = wmType.value;
            const usePgNum = document.getElementById('usePageNumber').checked;
            const canvasId = currentTab === 'single' ? 'wmCanvasSingle' : 'wmCanvasMerge';
            const boxId = currentTab === 'single' ? 'wmPreviewBoxSingle' : 'wmPreviewBoxMerge';
            const canvas = document.getElementById(canvasId);
            const box = document.getElementById(boxId);

            if (type === 'none' && !usePgNum) {
                box.classList.add('hidden');
                return;
            }

            box.classList.remove('hidden');
            const ctx = canvas.getContext('2d');
            const W = 600; const H = 848;
            canvas.width = W; canvas.height = H;
            ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
            ctx.globalAlpha = 0.08; ctx.fillStyle = '#000';
            for(let i=0; i<15; i++) { ctx.fillRect(W*0.1, 60 + (i*50), W*0.8, 12); ctx.fillRect(W*0.1, 85 + (i*50), W*0.5, 12); }
            ctx.globalAlpha = 1.0;

            if (usePgNum) {
                ctx.save(); ctx.globalAlpha = 0.5; ctx.font = "bold 20px 'Noto Sans KR'";
                ctx.fillStyle = "#6b7280"; ctx.textAlign = "center"; ctx.fillText("- Page 1 -", W/2, H - 40); ctx.restore();
            }

            if (type !== 'none') {
                const pos = document.getElementById('wmPosition').value;
                const size = parseInt(document.getElementById('wmSize').value);
                const opacity = parseInt(document.getElementById('wmOpacity').value) / 100;
                const rotation = parseInt(document.getElementById('wmRotation').value) * Math.PI / 180;
                const posMap = { 'center': [W/2, H/2], 'top-left': [W*0.15, H*0.1], 'top-right': [W*0.85, H*0.1], 'bottom-left': [W*0.15, H*0.9], 'bottom-right': [W*0.85, H*0.9] };
                const [cx, cy] = posMap[pos] || posMap['center'];
                ctx.save(); ctx.translate(cx, cy); ctx.rotate(rotation); ctx.globalAlpha = opacity;
                if (type === 'text') {
                    const text = document.getElementById('wmText').value || 'SIX SENSE';
                    ctx.font = `900 ${size * 0.8}px 'Noto Sans KR'`; ctx.fillStyle = '#4F46E5';
                    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 0);
                } else if (type === 'image' && wmLogoImg) {
                    const scale = size / 200;
                    ctx.drawImage(wmLogoImg, -(wmLogoImg.width*scale)/2, -(wmLogoImg.height*scale)/2, wmLogoImg.width*scale, wmLogoImg.height*scale);
                }
                ctx.restore();
            }
        }

        window.onload = () => {
            ['wmType', 'wmPosition', 'wmSize', 'wmOpacity', 'wmRotation', 'wmText', 'usePageNumber'].forEach(id => {
                const el = document.getElementById(id);
                if(el) el.addEventListener('input', () => drawWmPreview());
            });
            document.getElementById('wmImage').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if(file) {
                    const reader = new FileReader();
                    reader.onload = (event) => { wmLogoImg = new Image(); wmLogoImg.onload = drawWmPreview; wmLogoImg.src = event.target.result; };
                    reader.readAsDataURL(file);
                }
            });
        };

        wmType.onchange = () => {
            document.getElementById('wmTextGroup').classList.toggle('hidden', wmType.value !== 'text');
            document.getElementById('wmImageGroup').classList.toggle('hidden', wmType.value !== 'image');
            document.getElementById('wmAdvanced').classList.toggle('hidden', wmType.value === 'none');
            drawWmPreview();
        };

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('btnSingle').className = tab === 'single' ? "tab-btn active" : "tab-btn inactive";
            document.getElementById('btnMerge').className = tab === 'merge' ? "tab-btn active" : "tab-btn inactive";
            document.getElementById('sectionSingle').classList.toggle('hidden', tab !== 'single');
            document.getElementById('sectionMerge').classList.toggle('hidden', tab !== 'merge');
            drawWmPreview();
        }
        document.getElementById('btnSingle').onclick = () => switchTab('single');
        document.getElementById('btnMerge').onclick = () => switchTab('merge');

        function toggleEncryption() {
            const isChecked = document.getElementById('useEncryption').checked;
            const group = document.getElementById('encryptionGroup');
            const statusText = document.getElementById('encryptStatusText');
            group.classList.toggle('hidden', !isChecked);
            statusText.textContent = isChecked ? "활성화됨" : "사용 안 함";
            if(isChecked) statusText.classList.add('text-indigo-600');
            else statusText.classList.remove('text-indigo-600');
            if(!isChecked) document.getElementById('pdfPassword').value = "";
        }

        async function copyToClipboard() {
            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(currentDownloadUrl);
                } else {
                    const textArea = document.createElement("textarea");
                    textArea.value = currentDownloadUrl;
                    document.body.appendChild(textArea); textArea.select();
                    document.execCommand('copy'); document.body.removeChild(textArea);
                }
                const btn = document.getElementById('copyBtn');
                const txt = document.getElementById('copyBtnText');
                btn.style.backgroundColor = "#10B981"; btn.style.color = "white";
                txt.textContent = "복사 완료! ✅";
                showToast("링크가 클립보드에 복사되었습니다.", "success");
                setTimeout(() => { btn.style.backgroundColor = ""; btn.style.color = ""; txt.textContent = "S3 PDF 공유 링크 복사"; }, 2000);
            } catch (err) { showToast("복사 실패", "error"); }
        }

        function startExpiryTimer(sec) {
            if (timerInterval) clearInterval(timerInterval);
            let timer = sec;
            timerInterval = setInterval(() => {
                let m = parseInt(timer / 60, 10); let s = parseInt(timer % 60, 10);
                document.getElementById('expiryTimer').textContent = `${m < 10 ? "0"+m : m}:${s < 10 ? "0"+s : s} 후 자동 파기`;
                if (--timer < 0) { clearInterval(timerInterval); document.getElementById('expiryTimer').textContent = "만료됨"; }
            }, 1000);
        }

        function updateProgress(target, status, sub) {
            document.getElementById('loadingStatus').textContent = status;
            document.getElementById('loadingSubText').textContent = sub;
            document.getElementById('progressBar').style.width = target + '%';
            document.getElementById('percentText').textContent = target + '%';
        }

        function startFakeProgress() {
            let current = 0; updateProgress(5, "엔진 초기화", "작업을 준비하고 있습니다...");
            if (progressInterval) clearInterval(progressInterval);
            progressInterval = setInterval(() => { if (current < 90) { current += Math.floor(Math.random() * 5) + 1; updateProgress(current, "PDF 변환 및 압축 중", "SixSense 엔진 가동 중..."); } }, 500);
        }

        // 단일 파일 게이지 업데이트
        function updateSingleGauge(size) {
            const wrapper = document.getElementById('singleGaugeWrapper');
            const bar = document.getElementById('singleSizeBar');
            const label = document.getElementById('singleGaugeLabel');
            if (size > 0) {
                wrapper.classList.remove('hidden');
                const mb = (size / (1024 * 1024)).toFixed(1);
                const percent = Math.min((size / (50 * 1024 * 1024)) * 100, 100);
                bar.style.width = percent + '%';
                label.textContent = mb + ' MB / 50 MB';
                if (percent > 80) bar.classList.add('gauge-warning');
                else bar.classList.remove('gauge-warning');
            } else { wrapper.classList.add('hidden'); }
        }

        async function handleSingleUpload() {
            if(!singleFile) return showToast('파일을 선택해주세요.', 'error');
            const formData = new FormData();
            formData.append('file', singleFile);
            formData.append('wm_type', wmType.value);
            formData.append('wm_text', document.getElementById('wmText').value);
            formData.append('wm_position', document.getElementById('wmPosition').value);
            formData.append('wm_size', document.getElementById('wmSize').value);
            formData.append('wm_opacity', (document.getElementById('wmOpacity').value/100).toFixed(2));
            formData.append('wm_rotation', document.getElementById('wmRotation').value);
            if(document.getElementById('wmImage').files[0]) formData.append('wm_image', document.getElementById('wmImage').files[0]);
            if(document.getElementById('useEncryption').checked) formData.append('pdf_pw', document.getElementById('pdfPassword').value);
            formData.append('use_pg_num', document.getElementById('usePageNumber').checked);

            document.getElementById('loadingScreen').classList.remove('hidden');
            startFakeProgress();
            try {
                const res = await axios.post('/convert-single/', formData);
                currentDownloadUrl = res.data.download_url;
                document.getElementById('downloadLink').href = currentDownloadUrl;
                document.getElementById('resultArea').classList.remove('hidden');
                showToast("PDF 변환이 완료되었습니다!", "success");
                startExpiryTimer(300);
            } catch(e) {
                showToast("변환 중 오류가 발생했습니다.", "error");
            } finally { clearInterval(progressInterval); document.getElementById('loadingScreen').classList.add('hidden'); }
        }

        const inputSingle = document.getElementById('inputSingle');
        document.getElementById('dropZoneSingle').onclick = () => inputSingle.click();
        inputSingle.onchange = (e) => {
            const file = e.target.files[0];
            if(file && validateFile(file)) {
                singleFile = file;
                document.getElementById('nameSingle').textContent = file.name;
                document.getElementById('sizeSingle').textContent = formatSize(file.size);
                document.getElementById('infoSingle').classList.remove('hidden');
                updateSingleGauge(file.size);
                drawWmPreview();
                showToast(`${file.name} 업로드 준비 완료`, "info");
            }
        };

        function resetSingle() {
            singleFile = null; document.getElementById('inputSingle').value = '';
            document.getElementById('infoSingle').classList.add('hidden');
            updateSingleGauge(0);
            if(!document.getElementById('usePageNumber').checked) document.getElementById('wmPreviewBoxSingle').classList.add('hidden');
            drawWmPreview();
        }

        const listMerge = document.getElementById('listMerge');
        new Sortable(listMerge, { animation: 150 });
        document.getElementById('dropZoneMerge').onclick = () => document.getElementById('inputMerge').click();
        document.getElementById('inputMerge').onchange = (e) => {
            Array.from(e.target.files).forEach(f => { if(mergeFiles.length < 10 && validateFile(f)) { f.uniqueId = Date.now() + Math.random(); mergeFiles.push(f); } });
            updateMergeList();
        };

        function updateMergeList() {
            const totalBytes = mergeFiles.reduce((sum, f) => sum + f.size, 0);
            const totalMB = (totalBytes / (1024 * 1024)).toFixed(1);
            const percent = Math.min((totalBytes / (50 * 1024 * 1024)) * 100, 100);

            const wrapper = document.getElementById('gaugeWrapper');
            const bar = document.getElementById('sizeGaugeBar');
            const label = document.getElementById('gaugeLabel');

            if (mergeFiles.length > 0) {
                wrapper.classList.remove('hidden');
                bar.style.width = percent + '%';
                label.textContent = totalMB + ' MB / 50 MB';
                if (percent > 80) bar.classList.add('gauge-warning');
                else bar.classList.remove('gauge-warning');
            } else { wrapper.classList.add('hidden'); }

            document.getElementById('mergeStatus').textContent = `현재 ${mergeFiles.length}개 선택됨 (총 ${totalMB}MB)`;
            if(mergeFiles.length > 0) {
                listMerge.classList.remove('hidden');
                listMerge.innerHTML = mergeFiles.map(f => `
                    <div class="bg-white p-4 rounded-xl border flex justify-between items-center shadow-sm mb-2" data-id="${f.uniqueId}">
                        <div class="flex flex-col truncate pr-4 text-left">
                            <span class="text-sm font-bold truncate text-gray-800">${f.name}</span>
                            <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">${formatSize(f.size)}</span>
                        </div>
                        <button onclick="removeFile(${f.uniqueId})" class="text-red-400 font-bold px-2 hover:bg-red-50 rounded-lg transition">✕</button>
                    </div>
                `).join('');
            } else { listMerge.classList.add('hidden'); if(!document.getElementById('usePageNumber').checked) document.getElementById('wmPreviewBoxMerge').classList.add('hidden'); }
            drawWmPreview();
        }
        window.removeFile = (uid) => { mergeFiles = mergeFiles.filter(f => f.uniqueId !== uid); updateMergeList(); showToast("파일이 제거되었습니다.", "info"); };

        async function handleMergeUpload() {
            if(mergeFiles.length < 2) return showToast('2개 이상의 파일을 선택하세요.', 'error');
            const formData = new FormData();
            mergeFiles.forEach(f => formData.append('files', f));
            formData.append('wm_type', wmType.value);
            formData.append('wm_text', document.getElementById('wmText').value);
            formData.append('wm_position', document.getElementById('wmPosition').value);
            formData.append('wm_size', document.getElementById('wmSize').value);
            formData.append('wm_opacity', (document.getElementById('wmOpacity').value/100).toFixed(2));
            formData.append('wm_rotation', document.getElementById('wmRotation').value);
            if(document.getElementById('wmImage').files[0]) formData.append('wm_image', document.getElementById('wmImage').files[0]);
            if(document.getElementById('useEncryption').checked) formData.append('pdf_pw', document.getElementById('pdfPassword').value);
            formData.append('use_pg_num', document.getElementById('usePageNumber').checked);

            document.getElementById('loadingScreen').classList.remove('hidden');
            startFakeProgress();
            try {
                const res = await axios.post('/convert-merge/', formData);
                currentDownloadUrl = res.data.download_url;
                document.getElementById('downloadLink').href = currentDownloadUrl;
                document.getElementById('resultArea').classList.remove('hidden');
                showToast("통합 PDF 생성이 완료되었습니다!", "success");
                startExpiryTimer(300);
            } catch(e) {
                showToast("병합 중 오류가 발생했습니다.", "error");
            } finally { clearInterval(progressInterval); document.getElementById('loadingScreen').classList.add('hidden'); }
        }

        function validateFile(file) {
            const fileName = file.name.toLowerCase();
            const allowedExtensions = ['.png', '.jpg', '.jpeg', '.bmp', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt'];
            const ext = "." + file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(ext)) { showToast(`지원하지 않는 형식: ${ext}`, "error"); return false; }
            const limit = 50 * 1024 * 1024;
            if (file.size > limit) {
                showToast(`50MB 용량 제한 초과! (${(file.size / (1024 * 1024)).toFixed(1)}MB)`, "error");
                return false;
            }
            return true;
        }

        [document.getElementById('dropZoneSingle'), document.getElementById('dropZoneMerge')].forEach(dz => {
            dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('active'); });
            dz.addEventListener('dragleave', () => dz.classList.remove('active'));
            dz.addEventListener('drop', (e) => {
                e.preventDefault(); dz.classList.remove('active');
                const dropped = Array.from(e.dataTransfer.files);
                if(dz.id === 'dropZoneSingle') {
                    if(validateFile(dropped[0])) {
                        singleFile = dropped[0];
                        document.getElementById('nameSingle').textContent = singleFile.name;
                        document.getElementById('sizeSingle').textContent = formatSize(singleFile.size);
                        document.getElementById('infoSingle').classList.remove('hidden');
                        updateSingleGauge(singleFile.size);
                        showToast("파일 업로드 준비 완료", "info");
                    }
                } else {
                    dropped.forEach(f => { if(mergeFiles.length < 10 && validateFile(f)) { f.uniqueId = Date.now()+Math.random(); mergeFiles.push(f); } });
                    updateMergeList();
                }
                drawWmPreview();
            });
        });
    </script>
</body>
</html>
"""

# 최종 조립
HTML_CONTENT = HTML_HEADER + ABOUT_SECTION + API_SECTION + HTML_FOOTER
