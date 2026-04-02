# components.py

# SixSense의 기술적 깊이와 통합 브랜딩을 강조한 ABOUT 섹션
ABOUT_SECTION = """
        <section id="about" class="bg-white p-16 rounded-3xl shadow-xl border border-gray-100">
            <div class="text-center mb-16">
                <h2 class="text-5xl font-black text-gray-900 font-poppins">Infrastructure Depth</h2>
                <div class="title-underline" style="width: 60px; height: 5px; background: #6366F1; margin: 15px auto 0; border-radius: 10px;"></div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-5 gap-16 items-start">
                <div class="md:col-span-3 text-gray-700 text-lg leading-relaxed space-y-6 font-medium">
                    <p class="text-2xl font-black text-indigo-600 mb-4">"단순한 변환을 넘어, 엔지니어링의 정수를 담다."</p>
                    <p>SixSense의 모든 클라우드 자원은 <b>Terraform</b>을 통해 IaC(Infrastructure as Code)로 관리됩니다. 이를 통해 인프라의 무결성을 보장하며, <b>GitHub Actions</b> CI/CD 파이프라인을 통해 배포 전 <b>Trivy</b>와 <b>Checkov</b>로 이미지 및 코드의 보안 취약점을 자동 스캐닝합니다.</p>

                    <p>보안은 우리의 핵심 가치입니다. <b>WAF(ModSecurity)</b>를 적용하여 악의적인 웹 요청을 차단하며, <b>Snort IDS</b> 및 <b>netfilter IPS</b>를 구축하여 권한 없는 접근을 원천 봉쇄합니다. 또한 쿠버네티스 환경에서는 <b>Falco</b>를 통해 실시간 런타임 보안 감시 및 격리를 수행합니다.</p>

                    <p>이 모든 보안 관련 이벤트와 로그들은 <b>Kafka</b>를 통해 실시간 백업되며, <b>Grafana</b>를 통해 실시간으로 모니터링되어 사용자의 데이터가 처리되는 모든 순간을 보호합니다. 데이터는 <b>S3</b>에 격리 저장되며, <b>5분간 유효한 IAM Pre-signed URL</b> 배포 후 <b>5분 뒤 철저히 파기</b>됩니다.</p>

                    <div class="grid grid-cols-2 gap-4 mt-8">
                        <div class="p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                            <p class="text-sm font-black text-indigo-800"> 🏗️ IaC Automation</p>
                            <p class="text-xs text-indigo-600">Terraform 기반 리소스 관리</p>
                        </div>
                        <div class="p-4 bg-red-50 rounded-2xl border border-red-100">
                            <p class="text-sm font-black text-red-800">🛡️ DevSecOps</p>
                            <p class="text-xs text-red-600">Checkov & Trivy 보안 검증</p>
                        </div>
                    </div>
                </div>

                <div class="md:col-span-2">
                    <div class="infra-card shadow-2xl" style="background: #1E1B4B; color: #E0E7FF; border-radius: 2.5rem; padding: 2.5rem; border: 1px solid rgba(99, 102, 241, 0.3);">
                        <h3 class="text-2xl font-black mb-8 font-poppins text-white border-b border-indigo-500/50 pb-4 flex items-center">
                            <img src="/static/sixsenselogo.png" alt="SixSense" class="w-8 h-8 object-contain mr-3 rounded-md">
                            Core Infrastructure
                        </h3>
                        <div class="space-y-6">
                            <div>
                                <p class="text-indigo-400 text-xs font-black mb-2 uppercase tracking-widest">Orchestration & Cloud</p>
                                <ul class="space-y-2 text-sm font-bold">
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> K3s Cluster & EC2 Auto Scaling</li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> AWS S3 & IAM Pre-signed URL</li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> <b>Terraform (IaC Management)</b></li>
                                </ul>
                            </div>
                            <div>
                                <p class="text-indigo-400 text-xs font-black mb-2 uppercase tracking-widest">Secure Monitoring</p>
                                <ul class="space-y-2 text-sm font-bold">
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> WAF (ModSecurity) & Falco</li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> Snort IDS (Network Security)</li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> Prometheus & Grafana</li>
                                </ul>
                            </div>
                            <div>
                                <p class="text-indigo-400 text-xs font-black mb-2 uppercase tracking-widest">CI/CD & DevOps</p>
                                <ul class="space-y-2 text-sm font-bold">
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> GitHub Actions CI/CD Pipeline</li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> <b>Security Scan (Trivy, Checkov)</b></li>
                                    <li class="flex items-center"><span class="text-indigo-500 mr-2">✔</span> Kafka & Ansible Configuration</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
"""

# API 섹션
API_SECTION = """
        <section id="api" class="space-y-12">
            <div class="text-center">
                <h2 class="text-5xl font-black text-gray-900 font-poppins">Developer API</h2>
                <div class="title-underline" style="width: 60px; height: 5px; background: #6366F1; margin: 15px auto 0; border-radius: 10px;"></div>
            </div>
            <div class="api-box shadow-2xl" style="background: #111827; color: #A5B4FC; border-radius: 2rem; padding: 3rem; font-family: 'Courier New', monospace; position: relative; overflow: hidden;">
                <div class="api-label" style="position: absolute; top: 1.5rem; right: 2rem; font-size: 4rem; font-weight: 900; color: rgba(255,255,255,0.03); font-family: 'Poppins', sans-serif;">API</div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    <div class="space-y-8">
                        <div>
                            <p class="text-gray-500 font-bold mb-3">// Single File Convert</p>
                            <p class="font-black text-2xl tracking-tight"><span class="text-purple-400">POST</span> <span class="text-green-400">/convert-single/</span></p>
                        </div>
                        <div class="pl-6 border-l-4 border-gray-800 space-y-1 text-sm">
                            <p class="text-indigo-300 font-bold mb-2">Payload (multipart/form-data)</p>
                            <p class="text-gray-400">file: <span class="text-white">document.docx</span></p>
                            <p class="text-gray-400">wm_type: <span class="text-white">text | image (Optional)</span></p>
                            <p class="text-gray-400">wm_text: <span class="text-white">"SIX SENSE" (Optional)</span></p>
                        </div>
                    </div>
                    <div class="space-y-8">
                        <div>
                            <p class="text-gray-500 font-bold mb-3">// Multi-File Merge & Convert</p>
                            <p class="font-black text-2xl tracking-tight"><span class="text-purple-400">POST</span> <span class="text-green-400">/convert-merge/</span></p>
                        </div>
                        <div class="pl-6 border-l-4 border-gray-800 space-y-1 text-sm">
                            <p class="text-indigo-300 font-bold mb-2">Payload (multipart/form-data)</p>
                            <p class="text-gray-400">files: <span class="text-white">file1.pdf, file2.xlsx... (Array)</span></p>
                            <p class="text-gray-400">wm_type: <span class="text-white">text | image (Optional)</span></p>
                            <p class="text-gray-400">wm_text: <span class="text-white">"SIX SENSE" (Optional)</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
"""
