/**
 * Cliente Text-to-Speech simplificado
 * Maneja reproducción de audio desde Google TTS o Web Speech API
 */

class TTSClient {
    constructor() {
        this.audioQueue = [];
        this.isPlaying = false;
        this.enabled = true; // Control para activar/desactivar
    }
    
    async speak(text, options = {}) {
        if (!this.enabled) return;
        
        const voice = options.voice || 'es-PE-Standard-A';
        const speed = options.speed || 1.0;
        
        try {
            // Intentar usar API backend primero
            const response = await fetch('/api/voice/speak', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ text, voice, speed })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.method === 'google_tts') {
                    await this.playGoogleAudio(data.audio);
                } else {
                    this.playWebSpeech(text, speed);
                }
            } else {
                // Si falla el backend, usar Web Speech API
                this.playWebSpeech(text, speed);
            }
            
        } catch (error) {
            console.warn('[TTS] Fallback a Web Speech API:', error);
            this.playWebSpeech(text, speed);
        }
    }
    
    async playGoogleAudio(base64Audio) {
        return new Promise((resolve, reject) => {
            const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
            audio.onended = () => {
                this.isPlaying = false;
                resolve();
            };
            audio.onerror = (error) => {
                this.isPlaying = false;
                reject(error);
            };
            
            this.isPlaying = true;
            audio.play().catch(reject);
        });
    }
    
    playWebSpeech(text, speed) {
        if (!('speechSynthesis' in window)) {
            console.warn('[TTS] Web Speech API no disponible');
            return;
        }
        
        // Cancelar cualquier voz anterior
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'es-PE';
        utterance.rate = speed;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        
        // Buscar voz en español
        const voices = window.speechSynthesis.getVoices();
        const spanishVoice = voices.find(v => 
            v.lang.startsWith('es-PE') || 
            v.lang.startsWith('es-MX') || 
            v.lang.startsWith('es-ES')
        );
        if (spanishVoice) utterance.voice = spanishVoice;
        
        utterance.onend = () => {
            this.isPlaying = false;
        };
        
        utterance.onerror = (error) => {
            console.error('[TTS] Error:', error);
            this.isPlaying = false;
        };
        
        this.isPlaying = true;
        window.speechSynthesis.speak(utterance);
    }
    
    stop() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        this.isPlaying = false;
    }
    
    toggle() {
        this.enabled = !this.enabled;
        if (!this.enabled) {
            this.stop();
        }
        return this.enabled;
    }
}

// Instancia global
window.ttsClient = new TTSClient();

// Cargar voces cuando estén disponibles
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        const voices = window.speechSynthesis.getVoices();
        console.log('[TTS] Voces disponibles:', voices.length);
    };
}