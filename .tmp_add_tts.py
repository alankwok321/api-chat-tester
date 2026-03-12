from pathlib import Path
p = Path('/home/node/.openclaw/workspace/api-chat-tester/index.html')
html = p.read_text(encoding='utf-8')

if 'id="ttsModal"' in html:
    print('TTS modal already present; no changes.')
    raise SystemExit(0)

# 1) Add button in actions row
needle_actions = '<div class="actions-row">\n    <button class="btn btn-secondary" onclick="clearChat()">🗑 清除</button>\n    <button class="btn btn-secondary" onclick="exportChat()">📋 匯出</button>\n  </div>'
if needle_actions in html:
    repl_actions = '<div class="actions-row">\n    <button class="btn btn-secondary" onclick="clearChat()">🗑 清除</button>\n    <button class="btn btn-secondary" onclick="exportChat()">📋 匯出</button>\n    <button class="btn btn-secondary" onclick="openTtsModal()">🔊 TTS</button>\n  </div>'
    html = html.replace(needle_actions, repl_actions)
else:
    print('WARN: actions-row needle not found; skipping button insert')

# 2) Add TTS modal HTML after image modal
needle_image_modal = '</div>\n\n<script>'
if needle_image_modal in html:
    tts_modal = '''</div>

<div class="tts-modal" id="ttsModal" aria-hidden="true">
  <div class="tts-modal-backdrop" onclick="closeTtsModal()"></div>
  <div class="tts-modal-content">
    <div class="tts-modal-header">
      <div>
        <div class="tts-title">🔊 Text-to-Speech 測試</div>
        <div class="tts-sub">使用 OpenAI 相容端點：<code>/v1/audio/speech</code></div>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-secondary" onclick="closeTtsModal()">✕ 關閉</button>
      </div>
    </div>

    <div class="tts-form">
      <div class="tts-grid">
        <div>
          <label class="tts-label">TTS 模型</label>
          <input id="ttsModel" type="text" value="gpt-4o-mini-tts" placeholder="gpt-4o-mini-tts / tts-1" />
        </div>
        <div>
          <label class="tts-label">Voice</label>
          <select id="ttsVoice">
            <option value="alloy">alloy</option>
            <option value="verse">verse</option>
            <option value="aria">aria</option>
            <option value="sage">sage</option>
            <option value="coral">coral</option>
            <option value="ash">ash</option>
          </select>
        </div>
        <div>
          <label class="tts-label">格式</label>
          <select id="ttsFormat">
            <option value="mp3">mp3</option>
            <option value="wav">wav</option>
            <option value="opus">opus</option>
            <option value="aac">aac</option>
            <option value="flac">flac</option>
          </select>
        </div>
        <div>
          <label class="tts-label">Speed</label>
          <input id="ttsSpeed" type="number" min="0.25" max="4" step="0.05" value="1" />
        </div>
      </div>

      <div>
        <label class="tts-label">要朗讀的文字</label>
        <textarea id="ttsText" rows="5" placeholder="輸入要朗讀的內容..."></textarea>
      </div>

      <div class="tts-actions">
        <button class="btn btn-primary" onclick="runTts()">產生語音</button>
        <a class="btn btn-secondary" id="ttsDownload" download="tts.mp3" style="display:none;">⬇ 下載</a>
      </div>

      <audio id="ttsAudio" controls style="width:100%; display:none;"></audio>

      <div class="tts-hint">
        提醒：這是瀏覽器端直接呼叫 API。請用你信任的端點（需要 CORS 允許），不要把金鑰放在公開網站。
      </div>
    </div>
  </div>
</div>

<script>'''
    html = html.replace(needle_image_modal, tts_modal)
else:
    print('WARN: image modal needle not found; skipping modal insert')

# 3) Add CSS for modal before </style>
needle_style_end = '</style>'
css = '''

  /* TTS Modal */
  .tts-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 50; align-items: center; justify-content: center; padding: 18px; }
  .tts-modal.active { display: flex; }
  .tts-modal-backdrop { position: absolute; inset: 0; }
  .tts-modal-content {
    position: relative;
    width: min(980px, 92vw);
    max-height: 92vh;
    overflow: auto;
    background: var(--surface);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 18px;
    z-index: 1;
  }
  .tts-modal-header { display:flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }
  .tts-title { font-weight: 800; font-size: 16px; }
  .tts-sub { color: var(--text-dim); font-size: 12px; margin-top: 4px; }
  .tts-sub code { background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.12); }
  .tts-form { display:grid; gap: 12px; }
  .tts-grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
  .tts-label { display:block; font-size: 12px; color: var(--text-dim); margin-bottom: 6px; }
  .tts-form input, .tts-form select, .tts-form textarea {
    width: 100%; padding: 10px 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-size: 14px; outline: none;
  }
  .tts-actions { display:flex; gap: 10px; align-items: center; }
  .tts-hint { font-size: 12px; color: var(--text-dim); }
  @media (max-width: 900px) { .tts-grid { grid-template-columns: 1fr 1fr; } }
'''
if needle_style_end in html:
    html = html.replace(needle_style_end, css + '\n' + needle_style_end, 1)
else:
    print('WARN: </style> not found; skipping CSS insert')

# 4) Add JS helpers before </script>
needle_script_end = '</script>'
js = '''

// --- TTS support (OpenAI-compatible) ---
function getTtsSettingsKey(provider = getProvider()) {
  return 'api_chat_tester_tts_' + provider;
}

function openTtsModal() {
  document.getElementById('ttsModal').classList.add('active');
  document.getElementById('ttsModal').setAttribute('aria-hidden', 'false');
  loadTtsSettings();
}

function closeTtsModal() {
  document.getElementById('ttsModal').classList.remove('active');
  document.getElementById('ttsModal').setAttribute('aria-hidden', 'true');
}

function saveTtsSettings() {
  const provider = getProvider();
  const payload = {
    model: document.getElementById('ttsModel')?.value || '',
    voice: document.getElementById('ttsVoice')?.value || 'alloy',
    format: document.getElementById('ttsFormat')?.value || 'mp3',
    speed: document.getElementById('ttsSpeed')?.value || '1',
    text: document.getElementById('ttsText')?.value || ''
  };
  localStorage.setItem(getTtsSettingsKey(provider), JSON.stringify(payload));
}

function loadTtsSettings() {
  const provider = getProvider();
  const raw = localStorage.getItem(getTtsSettingsKey(provider));
  if (!raw) return;
  try {
    const saved = JSON.parse(raw);
    if (saved.model) document.getElementById('ttsModel').value = saved.model;
    if (saved.voice) document.getElementById('ttsVoice').value = saved.voice;
    if (saved.format) document.getElementById('ttsFormat').value = saved.format;
    if (saved.speed) document.getElementById('ttsSpeed').value = saved.speed;
    if (saved.text) document.getElementById('ttsText').value = saved.text;
  } catch (e) {
    console.warn('無法讀取 TTS 設定', e);
  }
}

async function runTts() {
  const provider = getProvider();
  if (provider === 'anthropic') {
    addMessageEl('system', '⚠️ Anthropic 不提供 /v1/audio/speech。請切換到 OpenAI 相容端點再試。');
    return;
  }

  const key = document.getElementById('apiKey').value.trim();
  if (!key) { alert('請輸入 API 金鑰'); return; }

  const endpoint = document.getElementById('endpoint').value.trim();
  const url = resolveOpenAIBaseUrl(endpoint) + '/audio/speech';

  const model = document.getElementById('ttsModel').value.trim() || 'gpt-4o-mini-tts';
  const voice = document.getElementById('ttsVoice').value;
  const response_format = document.getElementById('ttsFormat').value;
  const speed = Number(document.getElementById('ttsSpeed').value || 1);
  const input = document.getElementById('ttsText').value.trim();
  if (!input) { alert('請輸入要朗讀的文字'); return; }

  saveTtsSettings();

  const audioEl = document.getElementById('ttsAudio');
  const dl = document.getElementById('ttsDownload');
  audioEl.style.display = 'none';
  dl.style.display = 'none';

  addMessageEl('system', `🔊 TTS 呼叫\n端點: ${url}\n模型: ${model}\nvoice: ${voice}\nformat: ${response_format}\nspeed: ${speed}`);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`
      },
      body: JSON.stringify({ model, voice, input, response_format, speed })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || `HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);

    audioEl.src = objectUrl;
    audioEl.style.display = 'block';
    audioEl.play().catch(() => {});

    const ext = response_format || 'mp3';
    dl.href = objectUrl;
    dl.download = `tts.${ext}`;
    dl.style.display = 'inline-flex';

    addMessageEl('system', '✅ 已產生語音，可播放/下載');
  } catch (error) {
    addMessageEl('system', '❌ TTS 失敗：' + (error.message || error));
  }
}
'''
if needle_script_end in html:
    html = html.replace(needle_script_end, js + '\n' + needle_script_end, 1)

p.write_text(html, encoding='utf-8')
print('Patched index.html with TTS support')
