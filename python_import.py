import sys

if sys.version_info[0] < 3:
    print("Napaka: Skripta potrebuje Python 3.")
    sys.exit(1)


import os
import requests 
import re

script_url = "https://screenreaderjs.github.io/ScreenReaderJS/screen-reader.min.js"

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    
def yes_no_question(prompt):
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in ['y', 'n']:
            return answer == 'y'
        else:
            print("Izberite 'y' za nadaljevanje ali 'n' za preklic.")

def get_depth_difference(mainpath, testpath):
    mainpath = os.path.normpath(mainpath)
    testpath = os.path.normpath(testpath)

    mainpath_depth = mainpath.count(os.path.sep)
    testpath_depth = testpath.count(os.path.sep)

    depth_difference = testpath_depth - mainpath_depth

    return depth_difference
    
def remove_script_tag(html_content):

    html_content = re.sub(r'\n{1,}<!-- ScreenReader -->', '<!-- ScreenReader -->', html_content)
    
    pattern = r'<!-- ScreenReader -->\n<script\s+src="[^"]+"></script>\n'
    
    updated_html_content = re.sub(pattern, "", html_content)

    return updated_html_content 
    
def check_for_book_folder(current_folder, book_folder):
 
    book_path = os.path.join(current_folder, book_folder)
    last_folder = os.path.basename(current_folder)
     
    return os.path.exists(book_path) or last_folder == book_folder
    
def modify_file(file_path, base_directory, write_local, uninstall):
    
    file_path = os.path.abspath(file_path)
    base_directory = os.path.abspath(base_directory)

    if write_local:
        new_script = '\n<!-- ScreenReader -->\n<script src="../js/screen-reader.js"></script>\n'
    else:
        new_script = '\n<!-- ScreenReader -->\n<script src="'+script_url+'"></script>\n'
    
    depth_diff = get_depth_difference(base_directory,os.path.dirname(file_path))

    if depth_diff < 1:
        if write_local:
            new_script = '\n<!-- ScreenReader -->\n<script src="js/screen-reader.js"></script>\n'
        else:
            new_script = '\n<!-- ScreenReader -->\n<script src="'+script_url+'"></script>\n'
            
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    html_content = remove_script_tag(html_content);
    
    if new_script not in html_content:
        last_script_pos = html_content.rfind('<script')

        if last_script_pos != -1:
            
            if not uninstall:
                html_content = (html_content[:last_script_pos] + new_script + '\n' + html_content[last_script_pos:])
            else:
                html_content = (html_content[:last_script_pos] + '\n' + html_content[last_script_pos:])
                
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
         

def get_html_files(directory):
    paths=[]
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                paths.append(os.path.join(root, file))
    return paths

def find_js_folders(current_folder, max_depth, exclude_numeric_only=True):
    js_folders = []

    base_depth = current_folder.rstrip(os.path.sep).count(os.path.sep)

    for root, dirs, files in os.walk(current_folder):
        current_depth = root.rstrip(os.path.sep).count(os.path.sep) - base_depth
        
        if current_depth > max_depth:
            dirs[:] = []
            continue

        if exclude_numeric_only:
            dirs[:] = [d for d in dirs if not d.isdigit()]

        if 'js' in dirs:
            js_folders.append(os.path.join(root, 'js'))

    return js_folders

def write_js_to_file(current_folder, uninstall, max_depth=5):
    url = script_url
    js_folders = find_js_folders(current_folder, max_depth)
    
    if not uninstall:
        try:
            response = requests.get(url)
            response.raise_for_status()

            for js_folder in js_folders:
                js_file_path = os.path.join(js_folder, 'screen-reader.js')
                os.makedirs(js_folder, exist_ok=True)

                with open(js_file_path, 'w', encoding="utf-8") as file:
                    file.write(response.text)
                
            print(f"\nJavaScript uspešno zapisan. [Št. datotek: "+str(len(js_folders))+"]")

        except requests.exceptions.RequestException as e:
            print(f"Napaka povezave: {e}")
        except Exception as e:
            print(f"Napaka: {e}")
    
    else:
        try:
            for js_folder in js_folders:
                for filename in os.listdir(js_folder):
                    if filename == 'screen-reader.js':
                        file_path = os.path.join(js_folder, filename)
                        os.remove(file_path)
            print(f"\nJavaScript uspešno izbrisan. [Št. datotek: "+str(len(js_folders))+"]")
        except FileNotFoundError:
            print(f"Mapa ni bila najdena: {js_folder}")
        except PermissionError:
            print(f"Napaka dovoljena denied: {js_folder}")
        except Exception as e:
            print(f"Napaka: {e}")


def write_js_to_file_local(current_folder, uninstall, max_depth=5):

    js_code = """class ScreenReader{constructor(){this._debug=!1,this._notyf=null,this._synth=window.speechSynthesis,this._synth.cancel(),this._audioSettings=new AudioSettings,this._voices=[],this._readerStatus="false",this.isLocalStorageAvailable()&&(this._readerStatus=localStorage.getItem("toggleScreenReader")||"false",this._readerStatus=/^true$/i.test(this._readerStatus)),this._hoverDelayReading=1e3,this._localVoiceName="",this._textReplacements={},this._appStrings={noSlovenianVoice:"Ni slovenskega glasu.",readingStopped:"Branje besedila je prekinjeno.",readAll:"Prebrano bo celotno besedilo.<br>CTRL - prekinitev branja",readingEnabled:"Branje besedila je vključeno.",readingDisabled:"Branje besedila je izključeno.",readerStartFailed:"Branja ni mogoče začeti.",readerBtnTitle:"Branje besedila\\nBljižnica: CTRL+B",readerDenied:"Branje besedila je samodejno onemogočeno.",synthTitle:"Sinteza govora:",interrupted:"branje predčasno prekinjeno","not-allowed":"branje ni dovoljeno",voice:"Glas: ",readerName:"Govornik TTS",keysEnabled:"Bljižnice so vklopljene<br><br>ALT+N - vklop/izklop bralca<br>ALT+B - preberi vse<br>CTRL - prekinitev branja",keysDisabled:"Bljižnice so izklopljene"},this._lastElement=null,this._hoverTimeout=null,this._enableMouse=!0,this.initialize()}isLocalStorageAvailable(){var e="testKey-"+Date.now();try{return localStorage.setItem(e,e),localStorage.removeItem(e),!0}catch(e){return!1}}simulateKeyPress(){var e=document.createEvent("KeyboardEvent");e[void 0!==e.initKeyboardEvent?"initKeyboardEvent":"initKeyEvent"]("keydown",!0,!0,window,!1,!1,!1,!1,40,0),document.dispatchEvent(e)}selectSlovenianVoice(e){let t=null;for(let a=0;a<e.length;a++)if("sl-SI"===e[a].lang||e[a].lang.startsWith("sl")){if(e[a].name.includes("Lado")||e[a].name.includes("Hugo"))return e[a];t||(t=e[a]),this._debug&&console.log(e[a].name)}return t}replaceText(e){return this._textReplacements[e]||e}translateText(e){return this._appStrings[e]||e}getAllTextFromElement(e){if(!e)return[];let t=[],a="";return e.childNodes.forEach((s=>{s.nodeType===Node.TEXT_NODE||s.nodeType===Node.ELEMENT_NODE&&["SPAN","B","I","U"].includes(s.tagName)?a+=s.textContent.trim():s.nodeType===Node.ELEMENT_NODE&&(a&&(t.push([a,e]),a=""),t.push(...this.getAllTextFromElement(s)))})),a&&t.push([a,e]),t}speakTexts(e){screenReader._enableMouse=!1;let t=0;!function a(){if(t<e.length){if(screenReader._enableMouse)return void screenReader.speakMsg("");screenReader.speakMsg(e[t][0],e[t][1]),t++;const s=setInterval((()=>{screenReader._synth.speaking||(clearInterval(s),a())}),100)}else screenReader._enableMouse=!0}()}speakMsg(e,t=null){if(this._readerStatus){this._synth.cancel(),this._debug&&console.log(`Berem: ${e}`);var a=new SpeechSynthesisUtterance;let n=this.selectSlovenianVoice(this._voices);if(this._debug&&console.log(n.name),!n)return void this.playTTSExternal(e,t);var s;a.voice=n,a.text=e,a.volume=this._audioSettings.volume,a.rate=this._audioSettings.rate,a.pitch=this._audioSettings.pitch,a.onstart=e=>{if(t){var a=window.getComputedStyle(t).color;this._debug&&console.log("Barva:"+a),t.style.color="rgb(255, 255, 255)"===a||"rgba(255, 255, 255, 1)"===a||"white"===a?"yellow":"red"}s=e.timeStamp,this._debug&&console.log("Start:"+s)},a.onend=e=>{t&&(t.style.color=""),s=e.timeStamp-s,this._debug&&console.log("End:"+e.timeStamp),this._debug&&console.log("Diff:"+s/1e3+" s"),isNaN(s)&&this._notyf.error(this._appStrings.readerStartFailed)},a.onerror=e=>{"interrupted"===e.error||this._notyf.error(`${this._appStrings.synthTitle}<br>${this.translateText(e.error)}`),this._debug&&console.log(`Sinteza govora: ${e.error}`),t&&(t.style.color="")},this._synth.speak(a),this._debug&&console.log(this._synth)}}PopulateVoices(){this._voices=this._synth.getVoices()}injectButton(){var e=document.createElement("li"),t=document.createElement("a");t.href="#",t.title=this._appStrings.readerBtnTitle,t.id="readerBtn";var a=document.createElement("span");a.id="readerIcon",this._readerStatus?a.className="fa fa-volume-up":a.className="fa fa-volume-off",t.appendChild(a),e.appendChild(t);var s=null;const n=["#navbar .navbar-nav","#navbar",".navbar","nav","[role='navigation']","[class*='menu']","[id*='menu']"];for(let e of n){const t=document.querySelector(e);if(t){s=t;break}}s&&(s.appendChild(e),t.onclick=()=>{this._synth.speak(new SpeechSynthesisUtterance(""));const e=this._synth.speaking||this._synth.pending;this._debug&&console.log("Available:"+e),this._notyf.dismissAll(),this.speakMsg("");var t="false";this.isLocalStorageAvailable()&&(t=localStorage.getItem("toggleScreenReader"));var s=!("true"===t);this.isLocalStorageAvailable()&&localStorage.setItem("toggleScreenReader",s.toString()),this._debug&&console.log("Reader:",s),this._readerStatus=s,this._readerStatus=/^true$/i.test(this._readerStatus),this._readerStatus?this._notyf.success(this._appStrings.readingEnabled+"<br><br>"+this._appStrings.voice+"<br>"+this._localVoiceName):this._notyf.success(this._appStrings.readingDisabled),this._readerStatus?a.className="fa fa-volume-up":a.className="fa fa-volume-off"})}playTTSExternal(e,t){var a=document.getElementById("audio-player");a&&(a.pause(),a.remove());var s=new XMLHttpRequest;s.open("POST","https://s1.govornik.eu/",!0),s.setRequestHeader("Content-Type","application/x-www-form-urlencoded");var n="voice=lili&text="+encodeURIComponent(e)+"&source=SpletniUcbenik&version=2&format=mp3";s.responseType="blob",s.onload=function(){if(200===s.status){var e=s.response,a=URL.createObjectURL(e),n=document.createElement("audio");n.id="audio-player",n.style.display="none",n.autoplay=!0,n.src=a,n.addEventListener("play",(function(){if(t){var e=window.getComputedStyle(t).color;this._debug&&console.log("Barva:"+e),t.style.color="rgb(255, 255, 255)"===e||"rgba(255, 255, 255, 1)"===e||"white"===e?"yellow":"red"}})),n.addEventListener("ended",(function(){t&&(t.style.color="")})),n.addEventListener("abort",(function(){t.style.color=""})),n.addEventListener("pause",(function(){n.ended||(t.style.color="")})),document.body.appendChild(n),n.play().catch((e=>{console.log("Predajanje onemogočeno.")}))}else console.log("Napaka predvajanja: ",s.status),console.info(this._appStrings.noSlovenianVoice),this._notyf.error(this._appStrings.noSlovenianVoice)},s.onerror=function(){console.log("Napaka zahteve.")},s.send(n)}enableNotyf(){var e=document.createElement("link");e.rel="stylesheet",e.href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css",document.head.appendChild(e);var t=document.createElement("script");t.src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js",document.body.appendChild(t),setTimeout((()=>{this._notyf=new Notyf({duration:3500}),this.checkReader(),this._localVoiceName="";let e=screenReader.selectSlovenianVoice(screenReader._voices);this._localVoiceName=e?e.name:this._appStrings.readerName;let t=!1,a=!1,s=!1,n=!1,r=!1;screenReader.isLocalStorageAvailable()&&(r=localStorage.getItem("ScreenReaderToggleKeyboard")||"false",r=/^true$/i.test(r)),document.body.addEventListener("keydown",(function(e){if(e.ctrlKey&&!t&&r&&(t=!0,screenReader.speakMsg(""),screenReader._enableMouse=!0,screenReader.status&&(screenReader._notyf.dismissAll(),screenReader._notyf.success(screenReader._appStrings.readingStopped))),e.altKey&&"b"===e.key.toLowerCase()&&!n&&r){n=!0,screenReader._enableMouse=!1;let e=screenReader.getAllTextFromElement(document.querySelector("#page-content-wrapper")),t=e.findIndex((e=>e[0].includes("«")));-1!==t&&e.splice(t,e.length-t),screenReader._readerStatus?screenReader._notyf.success(screenReader._appStrings.readAll):screenReader._notyf.error(screenReader._appStrings.readingDisabled),screenReader.speakTexts(e)}e.altKey&&"n"===e.key.toLowerCase()&&!s&&r&&(s=!0,document.getElementById("readerIcon").click()),e.ctrlKey&&"b"===e.key.toLowerCase()&&!a&&(a=!0,r=!r,screenReader.isLocalStorageAvailable()&&localStorage.setItem("ScreenReaderToggleKeyboard",r),screenReader._notyf.dismissAll(),r?screenReader._notyf.success({message:screenReader._appStrings.keysEnabled,duration:2e4,dismissible:!0}):screenReader._notyf.success(screenReader._appStrings.keysDisabled))})),document.body.addEventListener("keyup",(function(e){!1!==e.altKey&&"n"!==e.key.toLowerCase()||(s=!1),!1!==e.altKey&&"b"!==e.key.toLowerCase()||(n=!1),!1!==e.ctrlKey&&"b"!==e.key.toLowerCase()||(a=!1),!1===e.ctrlKey&&(t=!1)}))}),500)}checkReader(){this._synth.speak(new SpeechSynthesisUtterance(""));const e=this._synth.speaking||this._synth.pending;e||localStorage.setItem("ScreenReaderToggleKeyboard","false"),this._debug&&console.log("Reader:",this._readerStatus),this._readerStatus&&(e||(document.getElementById("readerIcon").className="fa fa-volume-off",this._notyf.error(this._appStrings.readerDenied),this.isLocalStorageAvailable()&&(localStorage.setItem("toggleScreenReader","false"),localStorage.setItem("ScreenReaderToggleKeyboard","false")),this._readerStatus=!1))}get status(){return this._readerStatus}set hoverDelay(e){if(!(e>=100&&e<=5e3))throw new Error("Hover delay must be between 100ms and 5000ms.");this._hoverDelayReading=e}set audioSettings(e){if(!e)throw new Error("AudioSettings error.");this._audioSettings=e}set debug(e){if("boolean"!=typeof e)throw new Error("Not a boolean error.");this._debug=e}set textReplacements(e){if(!e)throw new Error("textReplacements error.");this._textReplacements=e}get textReplacements(){return this._textReplacements}get hoverDelay(){return this._hoverDelayReading}get audioSettings(){return this._audioSettings}handleHoverOrTouch(e){let t,a;if("mousemove"===e.type)t=e.clientX,a=e.clientY;else if("touchstart"===e.type||"touchmove"===e.type){const s=e.touches[0];t=s.clientX,a=s.clientY}var s=document.elementFromPoint(t,a);if(s!==this._lastElement)if(this._hoverTimeout&&clearTimeout(this._hoverTimeout),this._lastElement=s,this._enableMouse&&s&&s!==document.documentElement&&s!==document.body){let e="";s.innerText.trim()&&(e=s.innerText.trim()),"IMG"===s.tagName?e=s.alt||"Slika":"INPUT"===s.tagName?e=s.placeholder||s.title||"":"A"===s.tagName&&s.title&&(e=s.title),e=this.replaceText(e),s&&"DIV"===s.tagName&&!s.querySelector("p, h1, h2, h3")&&(this._hoverTimeout=setTimeout((()=>{e&&this.speakMsg(e,s)}),3*this._hoverDelayReading)),"DIV"!==s.tagName&&"UL"!==s.tagName&&"CENTER"!==s.tagName&&"TABLE"!==s.tagName&&(this._hoverTimeout=setTimeout((()=>{e&&this.speakMsg(e,s)}),this._hoverDelayReading))}else this._lastElement=null}initialize(){this.injectButton(),this.enableNotyf(),this.PopulateVoices(),this.simulateKeyPress(),void 0!==this._synth&&(this._synth.onvoiceschanged=()=>this.PopulateVoices()),document.addEventListener("mousemove",this.handleHoverOrTouch.bind(this),{passive:!0}),document.addEventListener("touchstart",this.handleHoverOrTouch.bind(this),{passive:!0}),document.addEventListener("touchmove",this.handleHoverOrTouch.bind(this),{passive:!0})}}class AudioSettings{constructor(){this._volume=1,this._pitch=1,this._rate=1}get volume(){return this._volume}set volume(e){if(!(e>=0&&e<=1))throw new Error("Volume must be between 0 and 1.");this._volume=e}get pitch(){return this._pitch}set pitch(e){if(!(e>=.5&&e<=2))throw new Error("Pitch must be between 0.5 and 2.");this._pitch=e}get rate(){return this._rate}set rate(e){if(!(e>=.5&&e<=2))throw new Error("Rate must be between 0.5 and 2.");this._rate=e}}const settings=new AudioSettings,screenReader=new ScreenReader;settings.volume=.5;const textReplacements={"«":"Prejšnje poglavje","»":"Naslednje poglavje","‹":"Nazaj","›":"Naprej","×":"Zapri"};ScreenReader.audioSettings=settings,screenReader.hoverDelay=500;let localVoiceAvailable=screenReader.selectSlovenianVoice(screenReader._voices);screenReader.hoverDelay=localVoiceAvailable?500:400,screenReader.textReplacements=textReplacements,screenReader.debug=!1; """
    
    js_folders = find_js_folders(current_folder, max_depth)
    
    if not uninstall:
        try:
            for js_folder in js_folders:
                
                js_file_path = os.path.join(js_folder, 'screen-reader.js')
                os.makedirs(os.path.dirname(js_file_path), exist_ok=True)
                
                with open(js_file_path, 'w', encoding="utf-8") as file:
                    file.write(js_code)
                
            print(f"\nJavaScript uspešno zapisan. [Št. datotek: "+str(len(js_folders))+"]")
        
        except PermissionError:
            print(f"Napaka dovoljenja: {js_folders}")
        except Exception as e:
            print(f"Napaka: {e}")
    
    else:
        
        try:
            for js_folder in js_folders:
                for filename in os.listdir(js_folder):
                    if filename == 'screen-reader.js':
                        file_path = os.path.join(js_folder, filename)
                        os.remove(file_path)
            print(f"\nJavaScript uspešno izbrisan. [Št. datotek: "+str(len(js_folders))+"]")
        except FileNotFoundError:
            print(f"Mapa ni bila najdena: {js_folder}")
        except PermissionError:
            print(f"Napaka dovoljena denied: {js_folder}")
        except Exception as e:
            print(f"Napaka: {e}")
    
def install_screenreader(uninstall = False):
    cls()
    
    if not uninstall:
        print("Namestitev ScreenReaderJS")
    else:
        print("Odstanitev ScreenReaderJS")
    print("="*40)
    
    current_script_path = os.path.abspath(__file__)
    current_folder = os.path.dirname(current_script_path)
    
    print("Trenutna mapa: "+current_folder)
    book_folder = input('Ime podmape učbenika [trenutno: '+os.path.basename(current_folder)+']: ') 
    if not book_folder.strip():
        book_folder = ""


    if check_for_book_folder(current_folder, book_folder):
        
        write_local = True
        use_online_script = False
        
        if not uninstall:
            use_online_script = yes_no_question("\nUporabi spletno verzijo ScreenReaderJS: \n"+script_url+"?")
            
            if use_online_script:
                write_local = not use_online_script
                
            #if use_online_script:
            #    write_local = not yes_no_question("\nV HTML zapiši zunanjo povezavo JavaScript: \n"+script_url+"?") 
        
        paths_full=get_html_files(current_folder)
        total_files = len(paths_full)
        
        if yes_no_question("\nNajdenih HTML datkotek: "+str(len(paths_full))+"\nAli želite nadaljevati?"):
            
            if use_online_script:
                write_js_to_file(current_folder, uninstall)
            else:
                write_js_to_file_local(current_folder, uninstall)
                
            print("\nPosodobitev HTML datotek:")
            for i, element in enumerate(paths_full, 1):
                modify_file(element, current_folder, write_local, uninstall)
                progress = i / total_files
                bar_length = 40
                block = int(round(bar_length * progress))
                progress_bar = f"[{'#' * block}{'-' * (bar_length - block)}] {i}/{total_files} datotek"
                print(progress_bar, end='\r')

            if not uninstall:
                print("\n\nScreenReader je uspešno dodan.")
            else:
                print("\n\nScreenReader je uspešno odstranjen.")

            
        else:
            print("Preklicano.")
    else:
        print("\nMape "+book_folder+" ni bilo mogoče najti.")
        
    input("\nPritisni Enter za nadaljevanje...")

def print_menu():
    print("="*40)
    print(" "*7 + "ScreenReaderJS glavni meni" + " "*10)
    print("="*40)
    print(" 1. Namesti ScreenReaderJS")
    print(" 2. Odstrani ScreenReaderJS")
    print(" 3. O programu")
    print(" 4. Izhod")
    print("="*40)

def main_menu():
    while True:
        cls()
        print_menu()
        
        choice = input("Izberi možnost [1-4]: ").strip()
        
        if choice == '1':
            install_screenreader()
        elif choice == '2':
            install_screenreader(uninstall = True)
        elif choice == '3':
            about()
        elif choice == '4':
            print("Izhod...")
            sys.exit(0)
            break
        else:
            pass

def uninstall_screenreader():
    print("\nUninstalling ScreenReader...")

def about():
    cls()
    print("O programu")
    print("="*40)
    print("Ta program je zasnovan za upravljanje namestitve ScreenReaderJS.")
    print("ScreenReaderJS lahko namestite, odstranite.")
    print("Avtor: Blaž Celin")
    print("="*40)
    input("\nPritisni Enter za nadaljevanje...")

if __name__ == "__main__":
    while True:
        try:
            main_menu()
        except KeyboardInterrupt:
            pass
