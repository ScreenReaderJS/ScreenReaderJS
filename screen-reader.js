/**
ScreenReader JS
 */

class ScreenReader {
    constructor() {
        this._debug = false;
        this._notyf = null;
        this._synth = window.speechSynthesis;
        this._synth.cancel();

        this._audioSettings = new AudioSettings();
        this._voices = [];

        this._readerStatus = "false";
        if (this.isLocalStorageAvailable()) {
            this._readerStatus = localStorage.getItem("toggleScreenReader") || "false";
            this._readerStatus = /^true$/i.test(this._readerStatus);
        }

        this._hoverDelayReading = 1000;
        this._localVoiceName = "";
        this._textReplacements = {};

        this._appStrings = {
            "noSlovenianVoice": "Ni slovenskega glasu.",
            "readingStopped": "Branje besedila je prekinjeno.",
            "readAll": "Prebrano bo celotno besedilo.<br>CTRL - prekinitev branja",
            "readingEnabled": "Branje besedila je vključeno.",
            "readingDisabled": "Branje besedila je izključeno.",
            "readerStartFailed": "Branja ni mogoče začeti.",
            "readerBtnTitle": "Branje besedila&#013;Bljižnica: CTRL+B",
            "readerDenied": "Branje besedila je samodejno onemogočeno.",
            "synthTitle": "Sinteza govora:",
            "interrupted": "branje predčasno prekinjeno",
            "not-allowed": "branje ni dovoljeno",
            "voice": "Glas: ",
            "readerName": "Govornik TTS",
            "keysEnabled": "Bljižnice so vklopljene<br><br>ALT+N - vklop/izklop bralca<br>ALT+B - preberi vse<br>CTRL - prekinitev branja",
            "keysDisabled": "Bljižnice so izklopljene",
        };

        this._lastElement = null;
        this._hoverTimeout = null;
        this._enableMouse = true;
        
        this.initialize();
    }

    isLocalStorageAvailable() {
        var t = 'testKey-' + Date.now();
        try {
            localStorage.setItem(t, t);
            localStorage.removeItem(t);
            return true;
        } catch (e) {
            return false;
        }
    }

    simulateKeyPress() {
        var keyboardEvent = document.createEvent("KeyboardEvent");
        var initMethod =
            typeof keyboardEvent.initKeyboardEvent !== "undefined"
             ? "initKeyboardEvent"
             : "initKeyEvent";

        keyboardEvent[initMethod](
            "keydown",
            true,
            true,
            window,
            false,
            false,
            false,
            false,
            40,
            0);
        document.dispatchEvent(keyboardEvent);
    }

    selectSlovenianVoice(voices) {
        let firstAvailableSlovenianVoice = null;
        for (let i = 0; i < voices.length; i++) {
            if (voices[i].lang === "sl-SI" || voices[i].lang.startsWith("sl")) {
                if (voices[i].name.includes("Lado") || voices[i].name.includes("Hugo")) {
                    return voices[i];
                }
                if (!firstAvailableSlovenianVoice) {
                    firstAvailableSlovenianVoice = voices[i];
                }
                if (this._debug)
                    console.log(voices[i].name);
            }
        }
        return firstAvailableSlovenianVoice;
    }

    replaceText(text) {
        return this._textReplacements[text] || text;
    }

    translateText(text) {
        return this._appStrings[text] || text;
    }

    getAllTextFromElement(element) {
        if (!element) return [];
        let result = [];
        let currentText = "";
        
        element.childNodes.forEach(node => {
            if (node.nodeType === Node.TEXT_NODE || 
                (node.nodeType === Node.ELEMENT_NODE && ['SPAN', 'B', 'I', 'U'].includes(node.tagName))) {
                currentText += node.textContent.trim();
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                if (currentText) {
                    result.push([currentText, element]);
                    currentText = "";
                }
                result.push(...this.getAllTextFromElement(node));
            }
        });
        
        if (currentText) {
            result.push([currentText, element]);
        }
        
        return result;
    }


speakTexts(texts) {
    screenReader._enableMouse = false;
    let i = 0;

    function speakNext() {
        if (i < texts.length) {
            
            if(screenReader._enableMouse){
                screenReader.speakMsg("");
                return;
            }
            
            screenReader.speakMsg(texts[i][0], texts[i][1]);
            i++;

            const interval = setInterval(() => {
                if (!screenReader._synth.speaking) {
                    clearInterval(interval);
                    speakNext();
                }
            }, 100);
        } else {
            screenReader._enableMouse = true; 
        }
    }

    speakNext();
}
    
    speakMsg(msg, element = null) {
        if (this._readerStatus) {
            this._synth.cancel();

            if (this._debug)
                console.log(`Berem: ${msg}`);

            var utter = new SpeechSynthesisUtterance();

            let selectedVoice = this.selectSlovenianVoice(this._voices);
            if (this._debug)
                console.log(selectedVoice.name);

            if (selectedVoice) {
                utter.voice = selectedVoice;
            } else {
                this.playTTSExternal(msg, element);
                return;
            }

            utter.text = msg;

            utter.volume = this._audioSettings.volume;
            utter.rate = this._audioSettings.rate;
            utter.pitch = this._audioSettings.pitch;

            var time;

            utter.onstart = (event) => {
                if (element) {
                    var computedStyle = window.getComputedStyle(element);
                    var color = computedStyle.color;
                    if (this._debug)
                        console.log("Barva:" + color);

                    if (
                        color === "rgb(255, 255, 255)" ||
                        color === "rgba(255, 255, 255, 1)" ||
                        color === "white") {
                        element.style.color = "yellow";
                    } else {
                        element.style.color = "red";
                    }
                }
                time = event.timeStamp;
                if (this._debug)
                    console.log("Start:" + time);
            };

            utter.onend = (event) => {
                if (element)
                    element.style.color = "";
                time = event.timeStamp - time;
                if (this._debug)
                    console.log("End:" + event.timeStamp);
                if (this._debug)
                    console.log("Diff:" + time / 1000 + " s");

                if (isNaN(time)) {
                    this._notyf.error(this._appStrings["readerStartFailed"]);
                }
            };

            utter.onerror = (event) => {
                if (event.error === "interrupted") {}
                else {
                    this._notyf.error(`${this._appStrings["synthTitle"]}<br>${this.translateText(event.error)}`);
                }

                if (this._debug)
                    console.log(`Sinteza govora: ${event.error}`);
                if (element)
                    element.style.color = "";
            };
            this._synth.speak(utter);

            if (this._debug)
                console.log(this._synth);
        }
    }

    PopulateVoices() {
        this._voices = this._synth.getVoices();
    }

    injectButton() {
        var newItem = document.createElement("li");
        var newLink = document.createElement("a");
        newLink.href = "#";
        newLink.title = this._appStrings["readerBtnTitle"];
        newLink.id = "readerBtn";

        var newIcon = document.createElement("span");
        newIcon.id = "readerIcon";
        if (this._readerStatus)
            newIcon.className = "fa fa-volume-up";
        else
            newIcon.className = "fa fa-volume-off";

        newLink.appendChild(newIcon);

        newItem.appendChild(newLink);

        var navbar = document.querySelector("#navbar .navbar-nav");
        navbar.appendChild(newItem);

        newLink.onclick = () => {
            this._synth.speak(new SpeechSynthesisUtterance(""));
            const worked = this._synth.speaking || this._synth.pending;
            if (this._debug)
                console.log("Available:" + worked);

            this._notyf.dismissAll();
            this.speakMsg("");

            var toggleValue = "false";
            if (this.isLocalStorageAvailable())
                toggleValue = localStorage.getItem("toggleScreenReader");

            var currentValue = toggleValue === "true";
            var newValue = !currentValue;

            if (this.isLocalStorageAvailable())
                localStorage.setItem("toggleScreenReader", newValue.toString());

            if (this._debug)
                console.log("Reader:", newValue);
            this._readerStatus = newValue;
            this._readerStatus = /^true$/i.test(this._readerStatus);

            if (this._readerStatus)
                this._notyf.success(this._appStrings["readingEnabled"] + "<br><br>" + this._appStrings["voice"] + "<br>" + this._localVoiceName);
            else
                this._notyf.success(this._appStrings["readingDisabled"]);

            if (this._readerStatus)
                newIcon.className = "fa fa-volume-up";
            else
                newIcon.className = "fa fa-volume-off";
        };
    }

    playTTSExternal(text, element) {

        var existingAudioPlayer = document.getElementById('audio-player');

        if (existingAudioPlayer) {
            existingAudioPlayer.pause();
            existingAudioPlayer.remove();
        }

        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'https://s1.govornik.eu/', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        var params = 'voice=lili&text=' + encodeURIComponent(text) + '&source=SpletniUcbenik&version=2&format=mp3';
        xhr.responseType = 'blob';

        xhr.onload = function () {
            if (xhr.status === 200) {
                var audioBlob = xhr.response;
                var audioUrl = URL.createObjectURL(audioBlob);

                var audioPlayer = document.createElement('audio');
                audioPlayer.id = 'audio-player';
                audioPlayer.style.display = 'none';
                audioPlayer.autoplay = true;
                audioPlayer.src = audioUrl;

                audioPlayer.addEventListener('play', function () {
                    if (element) {
                        var computedStyle = window.getComputedStyle(element);
                        var color = computedStyle.color;
                        if (this._debug)
                            console.log("Barva:" + color);

                        if (
                            color === "rgb(255, 255, 255)" ||
                            color === "rgba(255, 255, 255, 1)" ||
                            color === "white") {
                            element.style.color = "yellow";
                        } else {
                            element.style.color = "red";
                        }
                    }
                });

                audioPlayer.addEventListener('ended', function () {
                    if (element)
                        element.style.color = "";
                });
                audioPlayer.addEventListener('abort', function () {
                    element.style.color = "";
                });

                audioPlayer.addEventListener('pause', function () {
                    if (!audioPlayer.ended) {
                        element.style.color = "";
                    }
                });

                document.body.appendChild(audioPlayer);

                audioPlayer.play().catch(error => {
                    console.log("Predajanje onemogočeno.");
                });
            } else {
                console.log('Napaka predvajanja: ', xhr.status);
                console.info(this._appStrings["noSlovenianVoice"]);
                this._notyf.error(this._appStrings["noSlovenianVoice"]);
            }
        };

        xhr.onerror = function () {
            console.log('Napaka zahteve.');
        };

        xhr.send(params);
    }

    enableNotyf() {
        var link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css";
        document.head.appendChild(link);

        var script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js";
        document.body.appendChild(script);

        setTimeout(() => {
            this._notyf = new Notyf({
                duration: 2500
            });
            this.checkReader();
            this._localVoiceName = "";
            let localVoiceAvailable = screenReader.selectSlovenianVoice(screenReader._voices);
            if (localVoiceAvailable) {
                this._localVoiceName = localVoiceAvailable.name;
            } else {
                this._localVoiceName = this._appStrings["readerName"];
            }

            let ctrlPressed = false;
            let ctrlNPressed = false;
            let altNPressed = false;
            let altBPressed = false;
            let keyboardEnable = false;
            if (screenReader.isLocalStorageAvailable()) {
                keyboardEnable = localStorage.getItem("ScreenReaderToggleKeyboard") || "false";
                keyboardEnable = /^true$/i.test(keyboardEnable);
            }

            document.body.addEventListener("keydown", function (event) {

                if (event.ctrlKey && !ctrlPressed && keyboardEnable) {
                    ctrlPressed = true;
                    screenReader.speakMsg("");
                    screenReader._enableMouse = true;
                    if (screenReader.status) {
                        screenReader._notyf.dismissAll();
                        screenReader._notyf.success(screenReader._appStrings["readingStopped"]);
                    }

                }

                if (event.altKey && event.key.toLowerCase() === "b" && !altBPressed && keyboardEnable) {
                    altBPressed = true;
                    screenReader._enableMouse = false;
                    let allTextArray = screenReader.getAllTextFromElement(document.querySelector('#page-content-wrapper'));
                    
                    let i = allTextArray.findIndex(item => item[0].includes("«"));
                    if (i !== -1) {
                        allTextArray.splice(i, allTextArray.length - i);
                    }

                    if(!screenReader._readerStatus){
                        screenReader._notyf.error(screenReader._appStrings["readingDisabled"]);
                    }else{
                        screenReader._notyf.success(screenReader._appStrings["readAll"]);
                    }
                    screenReader.speakTexts(allTextArray);
                   
                }

                if (event.altKey && event.key.toLowerCase() === "n" && !altNPressed && keyboardEnable) {
                    altNPressed = true;
                    document.getElementById("readerIcon").click();
                }
                
                if (event.ctrlKey && event.key.toLowerCase() === "b" && !ctrlNPressed) {
                    ctrlNPressed = true;
                    keyboardEnable = !keyboardEnable;
                    if (screenReader.isLocalStorageAvailable())
                        localStorage.setItem("ScreenReaderToggleKeyboard", keyboardEnable);
                    console.log(keyboardEnable);

                    if (keyboardEnable)
                        screenReader._notyf.success(screenReader._appStrings["keysEnabled"],  duration: 10000,  dismissible: true);
                    else
                        screenReader._notyf.success(screenReader._appStrings["keysDisabled"]);

                }
            });

            document.body.addEventListener("keyup", function (event) {

                if (event.altKey === false || event.key.toLowerCase() === "n") {
                    altNPressed = false;
                }

                if (event.altKey === false || event.key.toLowerCase() === "b") {
                    altBPressed = false;
                }
                
                if (event.ctrlKey === false || event.key.toLowerCase() === "b") {
                    ctrlNPressed = false;
                }

                if (event.ctrlKey === false) {
                    ctrlPressed = false;
                }
            });

        }, 500);
    }

    checkReader() {
        this._synth.speak(new SpeechSynthesisUtterance(""));
        const worked = this._synth.speaking || this._synth.pending;
        if (!worked) {
            localStorage.setItem("ScreenReaderToggleKeyboard", "false");
        }
        if (this._debug)
            console.log("Reader:", this._readerStatus);
        if (this._readerStatus) {
            if (!worked) {
                document.getElementById("readerIcon").className = "fa fa-volume-off";
                this._notyf.error(this._appStrings["readerDenied"]);
                if (this.isLocalStorageAvailable()) {
                    localStorage.setItem("toggleScreenReader", "false");
                    localStorage.setItem("ScreenReaderToggleKeyboard", "false");
                }
                this._readerStatus = false;

            }
        }
    }

    get status() {
        return this._readerStatus;
    }

    set hoverDelay(value) {
        if (value >= 100 && value <= 5000) {
            this._hoverDelayReading = value;
        } else {
            throw new Error("Hover delay must be between 100ms and 5000ms.");
        }
    }

    set audioSettings(value) {
        if (value) {
            this._audioSettings = value;
        } else {
            throw new Error("AudioSettings error.");
        }
    }

    set debug(value) {
        if (typeof value == "boolean") {
            this._debug = value;
        } else {
            throw new Error("Not a boolean error.");
        }
    }

    set textReplacements(value) {
        if (value) {
            this._textReplacements = value;
        } else {
            throw new Error("textReplacements error.");
        }
    }

    get textReplacements() {
        return this._textReplacements;
    }

    get hoverDelay() {
        return this._hoverDelayReading;
    }

    get audioSettings() {
        return this._audioSettings;
    }

    handleHoverOrTouch(event) {
        let clientX,
        clientY;
        
        if (event.type === "mousemove") {
            clientX = event.clientX;
            clientY = event.clientY;
        } else if (event.type === "touchstart" || event.type === "touchmove") {
            const touch = event.touches[0];
            clientX = touch.clientX;
            clientY = touch.clientY;
        }

        var element = document.elementFromPoint(clientX, clientY);

        if (element !== this._lastElement) {
            if (this._hoverTimeout) {
                clearTimeout(this._hoverTimeout);
            }

            this._lastElement = element;

            if (this._enableMouse &&
                element &&
                element !== document.documentElement &&
                element !== document.body) {
                let text = "";

                //exc
                if (element.innerText.trim()) {
                    text = element.innerText.trim();
                }

                if (element.tagName === "IMG") {
                    text = element.alt || "Slika";
                } else if (element.tagName === "INPUT") {
                    text = element.placeholder || element.title || "";
                } else if (element.tagName === "A" && element.title) {
                    text = element.title;
                }

                text = this.replaceText(text);

                if (
                    element.tagName !== "DIV" &&
                    element.tagName !== "UL" &&
                    element.tagName !== "CENTER" &&
                    element.tagName !== "TABLE") {
                    this._hoverTimeout = setTimeout(() => {
                        if (text)
                            this.speakMsg(text, element);
                    }, this._hoverDelayReading);
                }
            } else {
                this._lastElement = null;
            }
        }
    }

    initialize() {
        this.injectButton();
        this.enableNotyf();

        this.PopulateVoices();
        this.simulateKeyPress();

        if (this._synth !== undefined) {
            this._synth.onvoiceschanged = () => this.PopulateVoices();
        }

        document.addEventListener("mousemove", this.handleHoverOrTouch.bind(this), {
            passive: true,
        });

        document.addEventListener("touchstart", this.handleHoverOrTouch.bind(this), {
            passive: true,
        });

        document.addEventListener("touchmove", this.handleHoverOrTouch.bind(this), {
            passive: true,
        });

    }
}

class AudioSettings {
    constructor() {
        this._volume = 1;
        this._pitch = 1;
        this._rate = 1;
    }

    get volume() {
        return this._volume;
    }

    set volume(value) {
        if (value >= 0 && value <= 1) {
            this._volume = value;
        } else {
            throw new Error("Volume must be between 0 and 1.");
        }
    }

    get pitch() {
        return this._pitch;
    }

    set pitch(value) {
        if (value >= 0.5 && value <= 2) {
            this._pitch = value;
        } else {
            throw new Error("Pitch must be between 0.5 and 2.");
        }
    }

    get rate() {
        return this._rate;
    }

    set rate(value) {
        if (value >= 0.5 && value <= 2) {
            this._rate = value;
        } else {
            throw new Error("Rate must be between 0.5 and 2.");
        }
    }
}

const settings = new AudioSettings();
const screenReader = new ScreenReader();
settings.volume = 0.5;

const textReplacements = {
    "«": "Prejšnje poglavje",
    "»": "Naslednje poglavje",
    "‹": "Nazaj",
    "›": "Naprej",
    "×": "Zapri",
};

ScreenReader.audioSettings = settings;
screenReader.hoverDelay = 500;

let localVoiceAvailable = screenReader.selectSlovenianVoice(screenReader._voices);
if (localVoiceAvailable)
    screenReader.hoverDelay = 500;
else
    screenReader.hoverDelay = 500;

screenReader.textReplacements = textReplacements;
screenReader.debug = false;
