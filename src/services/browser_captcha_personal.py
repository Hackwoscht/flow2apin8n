"""
BrowserAutomatisierungAbrufen reCAPTCHA token
Verwenden nodriver (undetected-chromedriver Nachfolger) ImplementierungAnti-ErkennungBrowser
UnterstuetztResident-Modus: fuerjedeStueck project_id Automatisch erstellenResident-Tab, SofortbeiGenerierung token
"""
import asyncio
import time
import os
import sys
import subprocess
from typing import Optional, Dict, Any

from ..core.logger import debug_logger
from ..core.config import config


# ==================== Docker Umgebungserkennung ====================
def _is_running_in_docker() -> bool:
    """istObin Docker GeraetinAusfuehren"""
    # Methode1: Pruefen /.dockerenv Datei
    if os.path.exists('/.dockerenv'):
        return True
    # Methode2: Pruefen cgroup
    try:
        with open('/proc/1/cgroup', 'r') as f:
            content = f.read()
            if 'docker' in content or 'kubepods' in content or 'containerd' in content:
                return True
    except:
        pass
    # Methode3: PruefenUmgebungsvariable
    if os.environ.get('DOCKER_CONTAINER') or os.environ.get('KUBERNETES_SERVICE_HOST'):
        return True
    return False


IS_DOCKER = _is_running_in_docker()


def _is_truthy_env(name: str) -> bool:
    """BestimmenUmgebungsvariableistObfuer true。"""
    value = os.environ.get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


ALLOW_DOCKER_HEADED = (
    _is_truthy_env("ALLOW_DOCKER_HEADED_CAPTCHA")
    or _is_truthy_env("ALLOW_DOCKER_BROWSER_CAPTCHA")
)
DOCKER_HEADED_BLOCKED = IS_DOCKER and not ALLOW_DOCKER_HEADED


# ==================== nodriver Automatische Installation ====================
def _run_pip_install(package: str, use_mirror: bool = False) -> bool:
    """Ausfuehren pip install Befehl
    
    Args:
        package: Name
        use_mirror: istObVerwendenLandinnerhalbMirror
    
    Returns:
        istObInstallierenErfolgreich
    """
    cmd = [sys.executable, '-m', 'pip', 'install', package]
    if use_mirror:
        cmd.extend(['-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'])
    
    try:
        debug_logger.log_info(f"[BrowserCaptcha] GeradeinInstallieren {package}...")
        print(f"[BrowserCaptcha] GeradeinInstallieren {package}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            debug_logger.log_info(f"[BrowserCaptcha] ✅ {package} InstallierenErfolgreich")
            print(f"[BrowserCaptcha] ✅ {package} InstallierenErfolgreich")
            return True
        else:
            debug_logger.log_warning(f"[BrowserCaptcha] {package} InstallierenFehlgeschlagen: {result.stderr[:200]}")
            return False
    except Exception as e:
        debug_logger.log_warning(f"[BrowserCaptcha] {package} InstallierenAusnahme: {e}")
        return False


def _ensure_nodriver_installed() -> bool:
    """Sicherstellen nodriver bereitsInstallieren
    
    Returns:
        istObInstallierenErfolgreich/bereitsInstallieren
    """
    try:
        import nodriver
        debug_logger.log_info("[BrowserCaptcha] nodriver bereitsInstallieren")
        return True
    except ImportError:
        pass
    
    debug_logger.log_info("[BrowserCaptcha] nodriver nichtInstallieren, oeffnenAnfangAutomatische Installation...")
    print("[BrowserCaptcha] nodriver nichtInstallieren, oeffnenAnfangAutomatische Installation...")
    
    # ZuerstVersuchenversuchenOffiziellQuelle
    if _run_pip_install('nodriver', use_mirror=False):
        return True
    
    # OffiziellQuelleFehlgeschlagen, VersuchenversuchenLandinnerhalbMirror
    debug_logger.log_info("[BrowserCaptcha] OffiziellQuelleInstallierenFehlgeschlagen, VersuchenversuchenLandinnerhalbMirror...")
    print("[BrowserCaptcha] OffiziellQuelleInstallierenFehlgeschlagen, VersuchenversuchenLandinnerhalbMirror...")
    if _run_pip_install('nodriver', use_mirror=True):
        return True
    
    debug_logger.log_error("[BrowserCaptcha] ❌ nodriver Automatische InstallationFehlgeschlagen, BitteManuellInstallieren: pip install nodriver")
    print("[BrowserCaptcha] ❌ nodriver Automatische InstallationFehlgeschlagen, BitteManuellInstallieren: pip install nodriver")
    return False


# VersuchenversuchenImportieren nodriver
uc = None
NODRIVER_AVAILABLE = False

if DOCKER_HEADED_BLOCKED:
    debug_logger.log_warning(
        "[BrowserCaptcha] auf Docker Umgebung, StandardDeaktiviereninnerhalbSetzenBrowser-Captcha-Loesung。"
        "wiebenoetigenAktivierenBitteSetzen ALLOW_DOCKER_HEADED_CAPTCHA=true, undEinreichenBereitstellen DISPLAY/Xvfb。"
    )
    print("[BrowserCaptcha] ⚠️ auf Docker Umgebung, StandardDeaktiviereninnerhalbSetzenBrowser-Captcha-Loesung")
    print("[BrowserCaptcha] wiebenoetigenAktivierenBitteSetzen ALLOW_DOCKER_HEADED_CAPTCHA=true, undEinreichenBereitstellen DISPLAY/Xvfb")
else:
    if IS_DOCKER and ALLOW_DOCKER_HEADED:
        debug_logger.log_warning(
            "[BrowserCaptcha] Docker innerhalbSetzenBrowser-Captcha-LoesungNameEinzelnbereitsAktivieren, BitteSicherstellen DISPLAY/Xvfb Verfuegbar"
        )
        print("[BrowserCaptcha] ✅ Docker innerhalbSetzenBrowser-Captcha-LoesungNameEinzelnbereitsAktivieren")
    if _ensure_nodriver_installed():
        try:
            import nodriver as uc
            NODRIVER_AVAILABLE = True
        except ImportError as e:
            debug_logger.log_error(f"[BrowserCaptcha] nodriver ImportierenFehlgeschlagen: {e}")
            print(f"[BrowserCaptcha] ❌ nodriver ImportierenFehlgeschlagen: {e}")


class ResidentTabInfo:
    """Resident-TabInformationenStruktur"""
    def __init__(self, tab, project_id: str):
        self.tab = tab
        self.project_id = project_id
        self.recaptcha_ready = False
        self.created_at = time.time()


class BrowserCaptchaService:
    """BrowserAutomatisierungAbrufen reCAPTCHA token(nodriver Headed-Modus)
    
    UnterstuetztZweiModus: 
    1. Resident-Modus (Resident Mode): fuerjedeStueck project_id Resident-Tab, SofortbeiGenerierung token
    2. Traditioneller Modus (Legacy Mode): jedeMalAnfrageErstellenneuTab (fallback)
    """

    _instance: Optional['BrowserCaptchaService'] = None
    _lock = asyncio.Lock()

    def __init__(self, db=None):
        """InitialisierenDienst"""
        self.headless = False  # nodriver Headed-Modus
        self.browser = None
        self._initialized = False
        self.website_key = "6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV"
        self.db = db
        # Persistentisieren profile Verzeichnis
        self.user_data_dir = os.path.join(os.getcwd(), "browser_data")
        
        # Resident-ModusschliessenAttribut (Unterstuetztviele project_id)
        self._resident_tabs: dict[str, 'ResidentTabInfo'] = {}  # project_id -> Resident-TabInformationen
        self._resident_lock = asyncio.Lock()  # SchuetzenResident-TabOperation
        
        # Kompatibelalt API(Beibehalten single resident AttributfuerUnterscheidenName)
        self.resident_project_id: Optional[str] = None  # RichtungnachKompatibel
        self.resident_tab = None                         # RichtungnachKompatibel
        self._running = False                            # RichtungnachKompatibel
        self._recaptcha_ready = False                    # RichtungnachKompatibel
        self._last_fingerprint: Optional[Dict[str, Any]] = None
        self._resident_error_streaks: dict[str, int] = {}
        # DefinitionSeiteCaptcha-LoesungResident(verwendenFuer score-test)
        self._custom_tabs: dict[str, Dict[str, Any]] = {}
        self._custom_lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls, db=None) -> 'BrowserCaptchaService':
        """AbrufenEinzelnBeispielInstanz"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db)
        return cls._instance
    
    def _check_available(self):
        """PruefenDienstistObVerfuegbar"""
        if DOCKER_HEADED_BLOCKED:
            raise RuntimeError(
                "auf Docker Umgebung, StandardDeaktiviereninnerhalbSetzenBrowser-Captcha-Loesung。"
                "wiebenoetigenAktivierenBitteSetzenUmgebungsvariable ALLOW_DOCKER_HEADED_CAPTCHA=true, undEinreichenBereitstellen DISPLAY/Xvfb。"
            )
        if IS_DOCKER and not os.environ.get("DISPLAY"):
            raise RuntimeError(
                "Docker innerhalbSetzenBrowser-Captcha-LoesungbereitsAktivieren, aber DISPLAY nichtSetzen。"
                "BitteSetzen DISPLAY(Beispielwie :99)undStarten Xvfb。"
            )
        if not NODRIVER_AVAILABLE or uc is None:
            raise RuntimeError(
                "nodriver nichtInstallierenOdernichtVerfuegbar。"
                "BitteManuellInstallieren: pip install nodriver"
            )

    async def initialize(self):
        """Initialisieren nodriver Browser"""
        # PruefenDienstistObVerfuegbar
        self._check_available()
        
        if self._initialized and self.browser:
            # PruefenBrowseristObImmer nochspeichernAktiv
            try:
                # VersuchenversuchenAbrufenBrowserInformationenValidierenspeichernAktiv
                if self.browser.stopped:
                    debug_logger.log_warning("[BrowserCaptcha] BrowserbereitsStoppen, ErneutneuInitialisieren...")
                    self._initialized = False
                else:
                    return
            except Exception:
                debug_logger.log_warning("[BrowserCaptcha] BrowserkeinAntwort, ErneutneuInitialisieren...")
                self._initialized = False

        try:
            debug_logger.log_info(f"[BrowserCaptcha] GeradeinStarten nodriver Browser (BenutzerAnzahlBasierend aufVerzeichnis: {self.user_data_dir})...")

            # Sicherstellen user_data_dir speichernin
            os.makedirs(self.user_data_dir, exist_ok=True)

            browser_executable_path = os.environ.get("BROWSER_EXECUTABLE_PATH", "").strip() or None
            if browser_executable_path:
                debug_logger.log_info(
                    f"[BrowserCaptcha] VerwendenAngegebenBrowserkannAusfuehrenDatei: {browser_executable_path}"
                )

            # Starten nodriver Browser
            self.browser = await uc.start(
                headless=self.headless,
                user_data_dir=self.user_data_dir,
                browser_executable_path=browser_executable_path,
                sandbox=False,  # nodriver benoetigenbrauchendieseParameterKommenDeaktivieren sandbox
                browser_args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--window-size=1280,720',
                    '--profile-directory=Default',  # Ueberspringen Profile AuswahlGeraetSeite
                ]
            )

            self._initialized = True
            debug_logger.log_info(f"[BrowserCaptcha] ✅ nodriver BrowserbereitsStarten (Profile: {self.user_data_dir})")

        except Exception as e:
            debug_logger.log_error(f"[BrowserCaptcha] ❌ BrowserStartenFehlgeschlagen: {str(e)}")
            raise

    # ========== Resident-Modus API ==========

    async def start_resident_mode(self, project_id: str):
        """StartenResident-Modus
        
        Args:
            project_id: verwendenFuerResidentProjekt ID
        """
        if self._running:
            debug_logger.log_warning("[BrowserCaptcha] Resident-ModusbereitsinAusfuehren")
            return
        
        await self.initialize()
        
        self.resident_project_id = project_id
        website_url = f"https://labs.google/fx/tools/flow/project/{project_id}"
        
        debug_logger.log_info(f"[BrowserCaptcha] StartenResident-Modus, ZugriffSeite: {website_url}")
        
        # ErstelleneinStueckUnabhaengigneuTab(nichtVerwenden main_tab, VermeidenwurdeZurueckempfangen)
        self.resident_tab = await self.browser.get(website_url, new_tab=True)
        
        debug_logger.log_info("[BrowserCaptcha] TabbereitsErstellen, WartenSeiteLaden...")
        
        # WartenSeiteLadenAbgeschlossen(MitRetryMaschine)
        page_loaded = False
        for retry in range(60):
            try:
                await asyncio.sleep(1)
                ready_state = await self.resident_tab.evaluate("document.readyState")
                debug_logger.log_info(f"[BrowserCaptcha] SeiteStatus: {ready_state} (Retry {retry + 1}/60)")
                if ready_state == "complete":
                    page_loaded = True
                    break
            except ConnectionRefusedError as e:
                debug_logger.log_warning(f"[BrowserCaptcha] TabVerbindungVerloren: {e}, VersuchenversuchenErneutneuAbrufen...")
                # TabkannkannbereitsSchliessen, VersuchenversuchenErneutneuErstellen
                try:
                    self.resident_tab = await self.browser.get(website_url, new_tab=True)
                    debug_logger.log_info("[BrowserCaptcha] bereitsErneutneuErstellenTab")
                except Exception as e2:
                    debug_logger.log_error(f"[BrowserCaptcha] ErneutneuErstellenTabFehlgeschlagen: {e2}")
                await asyncio.sleep(2)
            except Exception as e:
                debug_logger.log_warning(f"[BrowserCaptcha] WartenSeiteAusnahme: {e}, Retry {retry + 1}/15...")
                await asyncio.sleep(2)
        
        if not page_loaded:
            debug_logger.log_error("[BrowserCaptcha] SeiteLadenTimeout, Resident-ModusStartenFehlgeschlagen")
            return
        
        # Warten reCAPTCHA Laden
        self._recaptcha_ready = await self._wait_for_recaptcha(self.resident_tab)
        
        if not self._recaptcha_ready:
            debug_logger.log_error("[BrowserCaptcha] reCAPTCHA LadenFehlgeschlagen, Resident-ModusStartenFehlgeschlagen")
            return
        
        self._running = True
        debug_logger.log_info(f"[BrowserCaptcha] ✅ Resident-ModusbereitsStarten (project: {project_id})")

    async def stop_resident_mode(self, project_id: Optional[str] = None):
        """StoppenResident-Modus
        
        Args:
            project_id: AngegebenbrauchenSchliessen project_id, wieErgebnisfuer None dannSchliessenallehatResident-Tab
        """
        async with self._resident_lock:
            if project_id:
                # SchliessenAngegebenResident-Tab
                await self._close_resident_tab(project_id)
                self._resident_error_streaks.pop(project_id, None)
                debug_logger.log_info(f"[BrowserCaptcha] bereitsSchliessen project_id={project_id} Resident-Modus")
            else:
                # SchliessenallehatResident-Tab
                project_ids = list(self._resident_tabs.keys())
                for pid in project_ids:
                    resident_info = self._resident_tabs.pop(pid, None)
                    if resident_info and resident_info.tab:
                        try:
                            await resident_info.tab.close()
                        except Exception:
                            pass
                self._resident_error_streaks.clear()
                debug_logger.log_info(f"[BrowserCaptcha] bereitsSchliessenallehatResident-Tab (Insgesamt {len(project_ids)} Stueck)")
        
        # RichtungnachKompatibel: BereinigenaltAttribut
        if not self._running:
            return
        
        self._running = False
        if self.resident_tab:
            try:
                await self.resident_tab.close()
            except Exception:
                pass
            self.resident_tab = None
        
        self.resident_project_id = None
        self._recaptcha_ready = False

    async def _wait_for_document_ready(self, tab, retries: int = 30, interval_seconds: float = 1.0) -> bool:
        """WartenSeiteDokumentLadenAbgeschlossen。"""
        for _ in range(retries):
            try:
                ready_state = await tab.evaluate("document.readyState")
                if ready_state == "complete":
                    return True
            except Exception:
                pass
            await asyncio.sleep(interval_seconds)
        return False

    def _is_server_side_flow_error(self, error_text: str) -> bool:
        error_lower = (error_text or "").lower()
        return any(keyword in error_lower for keyword in [
            "http error 500",
            "public_error",
            "internal error",
            "reason=internal",
            "reason: internal",
            "\"reason\":\"internal\"",
            "server error",
            "upstream error",
        ])

    async def _clear_tab_site_storage(self, tab) -> Dict[str, Any]:
        """BereinigenwennvorSeiteLokalspeichernSpeichernStatus, aberBeibehalten cookies AnmeldenStatus。"""
        result = await tab.evaluate("""
            (async () => {
                const summary = {
                    local_storage_cleared: false,
                    session_storage_cleared: false,
                    cache_storage_deleted: [],
                    indexed_db_deleted: [],
                    indexed_db_errors: [],
                    service_worker_unregistered: 0,
                };

                try {
                    window.localStorage.clear();
                    summary.local_storage_cleared = true;
                } catch (e) {
                    summary.local_storage_error = String(e);
                }

                try {
                    window.sessionStorage.clear();
                    summary.session_storage_cleared = true;
                } catch (e) {
                    summary.session_storage_error = String(e);
                }

                try {
                    if (typeof caches !== 'undefined') {
                        const cacheKeys = await caches.keys();
                        for (const key of cacheKeys) {
                            const deleted = await caches.delete(key);
                            if (deleted) {
                                summary.cache_storage_deleted.push(key);
                            }
                        }
                    }
                } catch (e) {
                    summary.cache_storage_error = String(e);
                }

                try {
                    if (navigator.serviceWorker) {
                        const registrations = await navigator.serviceWorker.getRegistrations();
                        for (const registration of registrations) {
                            const ok = await registration.unregister();
                            if (ok) {
                                summary.service_worker_unregistered += 1;
                            }
                        }
                    }
                } catch (e) {
                    summary.service_worker_error = String(e);
                }

                try {
                    if (typeof indexedDB !== 'undefined' && typeof indexedDB.databases === 'function') {
                        const dbs = await indexedDB.databases();
                        const names = Array.from(new Set(
                            dbs
                                .map((item) => item && item.name)
                                .filter((name) => typeof name === 'string' && name)
                        ));
                        for (const name of names) {
                            try {
                                await new Promise((resolve) => {
                                    const request = indexedDB.deleteDatabase(name);
                                    request.onsuccess = () => resolve(true);
                                    request.onerror = () => resolve(false);
                                    request.onblocked = () => resolve(false);
                                });
                                summary.indexed_db_deleted.push(name);
                            } catch (e) {
                                summary.indexed_db_errors.push(`${name}: ${String(e)}`);
                            }
                        }
                    } else {
                        summary.indexed_db_unsupported = true;
                    }
                } catch (e) {
                    summary.indexed_db_errors.push(String(e));
                }

                return summary;
            })()
        """)
        return result if isinstance(result, dict) else {}

    async def _clear_resident_storage_and_reload(self, project_id: str) -> bool:
        """BereinigenResident-TabSeiteAnzahlBasierend aufundAktualisieren, VersuchenversuchenVor OrtSelbstheilung。"""
        async with self._resident_lock:
            resident_info = self._resident_tabs.get(project_id)

        if not resident_info or not resident_info.tab:
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} KeinhatkannBereinigenResident-Tab")
            return False

        try:
            cleanup_summary = await self._clear_tab_site_storage(resident_info.tab)
            debug_logger.log_warning(
                f"[BrowserCaptcha] project_id={project_id} bereitsBereinigenSeitespeichernSpeichern, VorbereitenAktualisierenWiederherstellen: {cleanup_summary}"
            )
        except Exception as e:
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BereinigenSeitespeichernSpeichernFehlgeschlagen: {e}")
            return False

        try:
            resident_info.recaptcha_ready = False
            await resident_info.tab.reload()
        except Exception as e:
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BereinigennachAktualisierenTabFehlgeschlagen: {e}")
            return False

        if not await self._wait_for_document_ready(resident_info.tab, retries=30, interval_seconds=1.0):
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BereinigennachSeiteLadenTimeout")
            return False

        resident_info.recaptcha_ready = await self._wait_for_recaptcha(resident_info.tab)
        if resident_info.recaptcha_ready:
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BereinigennachbereitsWiederherstellen reCAPTCHA")
            return True

        debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BereinigennachImmer nochkeinMethodeWiederherstellen reCAPTCHA")
        return False

    async def _recreate_resident_tab(self, project_id: str) -> bool:
        """SchliessenundNeuerstellungResident-Tab。"""
        async with self._resident_lock:
            await self._close_resident_tab(project_id)
            resident_info = await self._create_resident_tab(project_id)
            if resident_info is None:
                debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} NeuerstellungResident-TabFehlgeschlagen")
                return False
            self._resident_tabs[project_id] = resident_info
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} bereitsNeuerstellungResident-Tab")
            return True

    async def _restart_browser_for_project(self, project_id: str) -> bool:
        """NeustartGesamtStueck nodriver Browser, undWiederherstellenAngegeben project Resident-Tab。"""
        debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} VorbereitenNeustart nodriver BrowsermitWiederherstellen")
        await self.close()
        await self.initialize()

        async with self._resident_lock:
            resident_info = await self._create_resident_tab(project_id)
            if resident_info is None:
                debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BrowserNeustartnachWiederherstellenResident-TabFehlgeschlagen")
                return False
            self._resident_tabs[project_id] = resident_info
            debug_logger.log_warning(f"[BrowserCaptcha] project_id={project_id} BrowserNeustartnachbereitsWiederherstellenResident-Tab")
            return True

    async def report_flow_error(self, project_id: str, error_reason: str, error_message: str = ""):
        """UpstreamGenerierungSchnittstelleAusnahmebei, fuerResident-TabAusfuehrenSelbstheilungWiederherstellen。"""
        if not project_id:
            return

        streak = self._resident_error_streaks.get(project_id, 0) + 1
        self._resident_error_streaks[project_id] = streak
        error_text = f"{error_reason or ''} {error_message or ''}".strip()
        debug_logger.log_warning(
            f"[BrowserCaptcha] project_id={project_id} empfangenaufUpstreamAusnahme, streak={streak}, reason={error_reason}, detail={error_message[:200]}"
        )

        if not self._initialized or not self.browser:
            return

        if self._is_server_side_flow_error(error_text):
            recreate_threshold = max(2, int(getattr(config, "browser_personal_recreate_threshold", 2) or 2))
            restart_threshold = max(3, int(getattr(config, "browser_personal_restart_threshold", 3) or 3))

            if streak >= restart_threshold:
                await self._restart_browser_for_project(project_id)
                return
            if streak >= recreate_threshold:
                await self._recreate_resident_tab(project_id)
                return

            healed = await self._clear_resident_storage_and_reload(project_id)
            if not healed:
                await self._recreate_resident_tab(project_id)
            return

        await self._recreate_resident_tab(project_id)

    async def _wait_for_recaptcha(self, tab) -> bool:
        """Warten reCAPTCHA Laden
        
        Returns:
            True if reCAPTCHA loaded successfully
        """
        debug_logger.log_info("[BrowserCaptcha]  reCAPTCHA...")
        
        # Pruefen grecaptcha.enterprise.execute
        is_enterprise = await tab.evaluate(
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined' && typeof grecaptcha.enterprise.execute === 'function'"
        )
        
        if is_enterprise:
            debug_logger.log_info("[BrowserCaptcha] reCAPTCHA Enterprise bereitsLaden")
            return True
        
        # VersuchenversuchenInjizierenSkript
        debug_logger.log_info("[BrowserCaptcha] nichtauf reCAPTCHA, InjizierenSkript...")
        
        await tab.evaluate(f"""
            (() => {{
                if (document.querySelector('script[src*="recaptcha"]')) return;
                const script = document.createElement('script');
                script.src = 'https://www.google.com/recaptcha/api.js?render={self.website_key}';
                script.async = true;
                document.head.appendChild(script);
            }})()
        """)
        
        # WartenSkriptLaden
        await tab.sleep(3)
        
        # Polling-Warten reCAPTCHA Laden
        for i in range(20):
            is_enterprise = await tab.evaluate(
                "typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined' && typeof grecaptcha.enterprise.execute === 'function'"
            )
            
            if is_enterprise:
                debug_logger.log_info(f"[BrowserCaptcha] reCAPTCHA Enterprise bereitsLaden(Warten {i * 0.5} Sekunden)")
                return True
            await tab.sleep(0.5)
        
        debug_logger.log_warning("[BrowserCaptcha] reCAPTCHA LadenTimeout")
        return False

    async def _wait_for_custom_recaptcha(
        self,
        tab,
        website_key: str,
        enterprise: bool = False,
    ) -> bool:
        """WartenBeliebigSeite reCAPTCHA Laden, verwendenFuerAnzahlTest。"""
        debug_logger.log_info("[BrowserCaptcha] Definition reCAPTCHA...")

        ready_check = (
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined' && "
            "typeof grecaptcha.enterprise.execute === 'function'"
        ) if enterprise else (
            "typeof grecaptcha !== 'undefined' && typeof grecaptcha.execute === 'function'"
        )
        script_path = "recaptcha/enterprise.js" if enterprise else "recaptcha/api.js"
        label = "Enterprise" if enterprise else "V3"

        is_ready = await tab.evaluate(ready_check)
        if is_ready:
            debug_logger.log_info(f"[BrowserCaptcha] Definition reCAPTCHA {label} bereitsLaden")
            return True

        debug_logger.log_info("[BrowserCaptcha] nichtaufDefinition reCAPTCHA, InjizierenSkript...")
        await tab.evaluate(f"""
            (() => {{
                if (document.querySelector('script[src*="recaptcha"]')) return;
                const script = document.createElement('script');
                script.src = 'https://www.google.com/{script_path}?render={website_key}';
                script.async = true;
                document.head.appendChild(script);
            }})()
        """)

        await tab.sleep(3)
        for i in range(20):
            is_ready = await tab.evaluate(ready_check)
            if is_ready:
                debug_logger.log_info(f"[BrowserCaptcha] Definition reCAPTCHA {label} bereitsLaden(Warten {i * 0.5} Sekunden)")
                return True
            await tab.sleep(0.5)

        debug_logger.log_warning("[BrowserCaptcha] Definition reCAPTCHA LadenTimeout")
        return False

    async def _execute_recaptcha_on_tab(self, tab, action: str = "IMAGE_GENERATION") -> Optional[str]:
        """inAngegebenTabAusfuehren reCAPTCHA Abrufen token
        
        Args:
            tab: nodriver TabObjekt
            action: reCAPTCHA actionTyp (IMAGE_GENERATION Oder VIDEO_GENERATION)
            
        Returns:
            reCAPTCHA token Oder None
        """
        # GenerierungEindeutigAendernMengeNameVermeidenKonflikt
        ts = int(time.time() * 1000)
        token_var = f"_recaptcha_token_{ts}"
        error_var = f"_recaptcha_error_{ts}"
        
        execute_script = f"""
            (() => {{
                window.{token_var} = null;
                window.{error_var} = null;
                
                try {{
                    grecaptcha.enterprise.ready(function() {{
                        grecaptcha.enterprise.execute('{self.website_key}', {{action: '{action}'}})
                            .then(function(token) {{
                                window.{token_var} = token;
                            }})
                            .catch(function(err) {{
                                window.{error_var} = err.message || 'execute failed';
                            }});
                    }});
                }} catch (e) {{
                    window.{error_var} = e.message || 'exception';
                }}
            }})()
        """
        
        # InjizierenAusfuehrenSkript
        await tab.evaluate(execute_script)
        
        # Polling-WartenErgebnisErgebnis(Am meistenviele 15 Sekunden)
        token = None
        for i in range(30):
            await tab.sleep(0.5)
            token = await tab.evaluate(f"window.{token_var}")
            if token:
                break
            error = await tab.evaluate(f"window.{error_var}")
            if error:
                debug_logger.log_error(f"[BrowserCaptcha] reCAPTCHA Fehler: {error}")
                break
        
        # BereinigenTemporaerbeiAendernMenge
        try:
            await tab.evaluate(f"delete window.{token_var}; delete window.{error_var};")
        except:
            pass
        
        return token

    async def _execute_custom_recaptcha_on_tab(
        self,
        tab,
        website_key: str,
        action: str = "homepage",
        enterprise: bool = False,
    ) -> Optional[str]:
        """inAngegebenTabAusfuehrenBeliebigSeite reCAPTCHA。"""
        ts = int(time.time() * 1000)
        token_var = f"_custom_recaptcha_token_{ts}"
        error_var = f"_custom_recaptcha_error_{ts}"
        execute_target = "grecaptcha.enterprise.execute" if enterprise else "grecaptcha.execute"

        execute_script = f"""
            (() => {{
                window.{token_var} = null;
                window.{error_var} = null;

                try {{
                    grecaptcha.ready(function() {{
                        {execute_target}('{website_key}', {{action: '{action}'}})
                            .then(function(token) {{
                                window.{token_var} = token;
                            }})
                            .catch(function(err) {{
                                window.{error_var} = err.message || 'execute failed';
                            }});
                    }});
                }} catch (e) {{
                    window.{error_var} = e.message || 'exception';
                }}
            }})()
        """

        await tab.evaluate(execute_script)

        token = None
        for _ in range(30):
            await tab.sleep(0.5)
            token = await tab.evaluate(f"window.{token_var}")
            if token:
                break
            error = await tab.evaluate(f"window.{error_var}")
            if error:
                debug_logger.log_error(f"[BrowserCaptcha] Definition reCAPTCHA Fehler: {error}")
                break

        try:
            await tab.evaluate(f"delete window.{token_var}; delete window.{error_var};")
        except:
            pass

        if token:
            post_wait_seconds = 3
            try:
                post_wait_seconds = float(getattr(config, "browser_recaptcha_settle_seconds", 3) or 3)
            except Exception:
                pass
            if post_wait_seconds > 0:
                debug_logger.log_info(
                    f"[BrowserCaptcha] Definition reCAPTCHA bereitsAbgeschlossen, ZusaetzlichausserhalbWarten {post_wait_seconds:.1f}s nachZurueckgeben token"
                )
                await tab.sleep(post_wait_seconds)

        return token

    async def _verify_score_on_tab(self, tab, token: str, verify_url: str) -> Dict[str, Any]:
        """DirektlesenabrufenTestSeiteAnzeigenAnzahl, Vermeiden verify.php mitSeiteAnzeigenKalibernichtKonsistent。"""
        _ = token
        _ = verify_url
        started_at = time.time()
        timeout_seconds = 25.0
        refresh_clicked = False
        last_snapshot: Dict[str, Any] = {}

        try:
            timeout_seconds = float(getattr(config, "browser_score_dom_wait_seconds", 25) or 25)
        except Exception:
            pass

        while (time.time() - started_at) < timeout_seconds:
            try:
                result = await tab.evaluate("""
                    (() => {
                        const bodyText = ((document.body && document.body.innerText) || "")
                            .replace(/\\u00a0/g, " ")
                            .replace(/\\r/g, "");
                        const patterns = [
                            { source: "current_score", regex: /Your score is:\\s*([01](?:\\.\\d+)?)/i },
                            { source: "selected_score", regex: /Selected Score Test:[\\s\\S]{0,400}?Score:\\s*([01](?:\\.\\d+)?)/i },
                            { source: "history_score", regex: /(?:^|\\n)\\s*Score:\\s*([01](?:\\.\\d+)?)\\s*;/i },
                        ];
                        let score = null;
                        let source = "";
                        for (const item of patterns) {
                            const match = bodyText.match(item.regex);
                            if (!match) continue;
                            const parsed = Number(match[1]);
                            if (!Number.isNaN(parsed) && parsed >= 0 && parsed <= 1) {
                                score = parsed;
                                source = item.source;
                                break;
                            }
                        }
                        const uaMatch = bodyText.match(/Current User Agent:\\s*([^\\n]+)/i);
                        const ipMatch = bodyText.match(/Current IP Address:\\s*([^\\n]+)/i);
                        return {
                            score,
                            source,
                            raw_text: bodyText.slice(0, 4000),
                            current_user_agent: uaMatch ? uaMatch[1].trim() : "",
                            current_ip_address: ipMatch ? ipMatch[1].trim() : "",
                            title: document.title || "",
                            url: location.href || "",
                        };
                    })()
                """)
            except Exception as e:
                result = {"error": f"{type(e).__name__}: {str(e)[:200]}"}

            if isinstance(result, dict):
                last_snapshot = result
                score = result.get("score")
                if isinstance(score, (int, float)):
                    elapsed_ms = int((time.time() - started_at) * 1000)
                    return {
                        "verify_mode": "browser_page_dom",
                        "verify_elapsed_ms": elapsed_ms,
                        "verify_http_status": None,
                        "verify_result": {
                            "success": True,
                            "score": score,
                            "source": result.get("source") or "antcpt_dom",
                            "raw_text": result.get("raw_text") or "",
                            "current_user_agent": result.get("current_user_agent") or "",
                            "current_ip_address": result.get("current_ip_address") or "",
                            "page_title": result.get("title") or "",
                            "page_url": result.get("url") or "",
                        },
                    }

            if not refresh_clicked and (time.time() - started_at) >= 2:
                refresh_clicked = True
                try:
                    await tab.evaluate("""
                        (() => {
                            const nodes = Array.from(
                                document.querySelectorAll('button, input[type="button"], input[type="submit"], a')
                            );
                            const target = nodes.find((node) => {
                                const text = (node.innerText || node.textContent || node.value || "").trim();
                                return /Refresh score now!?/i.test(text);
                            });
                            if (target) {
                                target.click();
                                return true;
                            }
                            return false;
                        })()
                    """)
                except Exception:
                    pass

            await tab.sleep(0.5)

        elapsed_ms = int((time.time() - started_at) * 1000)
        if not isinstance(last_snapshot, dict):
            last_snapshot = {"raw": last_snapshot}

        return {
            "verify_mode": "browser_page_dom",
            "verify_elapsed_ms": elapsed_ms,
            "verify_http_status": None,
            "verify_result": {
                "success": False,
                "score": None,
                "source": "antcpt_dom_timeout",
                "raw_text": last_snapshot.get("raw_text") or "",
                "current_user_agent": last_snapshot.get("current_user_agent") or "",
                "current_ip_address": last_snapshot.get("current_ip_address") or "",
                "page_title": last_snapshot.get("title") or "",
                "page_url": last_snapshot.get("url") or "",
                "error": last_snapshot.get("error") or "nichtinSeiteinlesenabrufenaufAnzahl",
            },
        }

    async def _extract_tab_fingerprint(self, tab) -> Optional[Dict[str, Any]]:
        """von nodriver TabExtrahierenBrowser-FingerabdruckInformationen。"""
        try:
            fingerprint = await tab.evaluate("""
                () => {
                    const ua = navigator.userAgent || "";
                    const lang = navigator.language || "";
                    const uaData = navigator.userAgentData || null;
                    let secChUa = "";
                    let secChUaMobile = "";
                    let secChUaPlatform = "";

                    if (uaData) {
                        if (Array.isArray(uaData.brands) && uaData.brands.length > 0) {
                            secChUa = uaData.brands
                                .map((item) => `"${item.brand}";v="${item.version}"`)
                                .join(", ");
                        }
                        secChUaMobile = uaData.mobile ? "?1" : "?0";
                        if (uaData.platform) {
                            secChUaPlatform = `"${uaData.platform}"`;
                        }
                    }

                    return {
                        user_agent: ua,
                        accept_language: lang,
                        sec_ch_ua: secChUa,
                        sec_ch_ua_mobile: secChUaMobile,
                        sec_ch_ua_platform: secChUaPlatform,
                    };
                }
            """)
            if not isinstance(fingerprint, dict):
                return None

            # personal ModuswennvornichtEinzelnUnabhaengigKonfigurationBrowserProxy, AnzeigenFormatVerwendendirektVerbinden, VermeidenmitalleProxyVerwechslung。
            result: Dict[str, Any] = {"proxy_url": None}
            for key in ("user_agent", "accept_language", "sec_ch_ua", "sec_ch_ua_mobile", "sec_ch_ua_platform"):
                value = fingerprint.get(key)
                if isinstance(value, str) and value:
                    result[key] = value
            return result
        except Exception as e:
            debug_logger.log_warning(f"[BrowserCaptcha] Extrahieren nodriver ZeigenFingerabdruckFehlgeschlagen: {e}")
            return None

    # ========== brauchen API ==========

    async def get_token(self, project_id: str, action: str = "IMAGE_GENERATION") -> Optional[str]:
        """Abrufen reCAPTCHA token
        
        AutomatischResident-Modus: wieErgebnisdiese project_id KeinhatResident-Tab, dannAutomatisch erstellenundResident
        
        Args:
            project_id: FlowProjektID
            action: reCAPTCHA actionTyp
                - IMAGE_GENERATION: Bild-GenerierungUnd2K/4KBild-Upscale (Standard)
                - VIDEO_GENERATION: Video-GenerierungUndVideo-Upscale

        Returns:
            reCAPTCHA tokenString, wieErgebnisAbrufenFehlgeschlagenZurueckgebenNone
        """
        # SicherstellenBrowserbereitsInitialisieren
        await self.initialize()
        self._last_fingerprint = None
        
        # VersuchenversuchenvonResident-TabAbrufen token
        async with self._resident_lock:
            resident_info = self._resident_tabs.get(project_id)
            
            # wieErgebnisdiese project_id KeinhatResident-Tab, dannAutomatisch erstellen
            if resident_info is None:
                debug_logger.log_info(f"[BrowserCaptcha] project_id={project_id} KeinhatResident-Tab, GeradeinErstellen...")
                resident_info = await self._create_resident_tab(project_id)
                if resident_info is None:
                    debug_logger.log_warning(f"[BrowserCaptcha] keinMethodefuer project_id={project_id} ErstellenResident-Tab, fallback aufTraditioneller Modus")
                    return await self._get_token_legacy(project_id, action)
                self._resident_tabs[project_id] = resident_info
                debug_logger.log_info(f"[BrowserCaptcha] ✅ bereitsfuer project_id={project_id} ErstellenResident-Tab (wennvorInsgesamt {len(self._resident_tabs)} Stueck)")
        
        # VerwendenResident-TabGenerierung token
        if resident_info and resident_info.recaptcha_ready and resident_info.tab:
            start_time = time.time()
            debug_logger.log_info(f"[BrowserCaptcha] vonResident-TabSofortbeiGenerierung token (project: {project_id}, action: {action})...")
            try:
                token = await self._execute_recaptcha_on_tab(resident_info.tab, action)
                duration_ms = (time.time() - start_time) * 1000
                if token:
                    self._resident_error_streaks.pop(project_id, None)
                    self._last_fingerprint = await self._extract_tab_fingerprint(resident_info.tab)
                    debug_logger.log_info(f"[BrowserCaptcha] ✅ TokenGenerierungErfolgreich(Verbrauchenbei {duration_ms:.0f}ms)")
                    return token
                else:
                    debug_logger.log_warning(f"[BrowserCaptcha] Resident-TabGenerierungFehlgeschlagen (project: {project_id}), VersuchenversuchenNeuerstellung...")
            except Exception as e:
                debug_logger.log_warning(f"[BrowserCaptcha] Resident-TabAusnahme: {e}, VersuchenversuchenNeuerstellung...")
            
            # Resident-TabUngueltig, VersuchenversuchenNeuerstellung
            async with self._resident_lock:
                await self._close_resident_tab(project_id)
                resident_info = await self._create_resident_tab(project_id)
                if resident_info:
                    self._resident_tabs[project_id] = resident_info
                    # NeuerstellungnachSofortSofortVersuchenversuchenGenerierung
                    try:
                        token = await self._execute_recaptcha_on_tab(resident_info.tab, action)
                        if token:
                            self._resident_error_streaks.pop(project_id, None)
                            self._last_fingerprint = await self._extract_tab_fingerprint(resident_info.tab)
                            debug_logger.log_info(f"[BrowserCaptcha] ✅ Neuerstellungnach TokenGenerierungErfolgreich")
                            return token
                    except Exception:
                        pass
        
        # Am meistenEndgueltig Fallback: VerwendenTraditioneller Modus
        debug_logger.log_warning(f"[BrowserCaptcha] allehatResidentFormatFehlgeschlagen, fallback aufTraditioneller Modus (project: {project_id})")
        legacy_token = await self._get_token_legacy(project_id, action)
        if legacy_token:
            self._resident_error_streaks.pop(project_id, None)
        return legacy_token

    async def _create_resident_tab(self, project_id: str) -> Optional[ResidentTabInfo]:
        """fuerAngegeben project_id ErstellenResident-Tab
        
        Args:
            project_id: Projekt ID
            
        Returns:
            ResidentTabInfo Objekt, Oder None(ErstellenFehlgeschlagen)
        """
        try:
            website_url = f"https://labs.google/fx/tools/flow/project/{project_id}"
            debug_logger.log_info(f"[BrowserCaptcha] fuer project_id={project_id} ErstellenResident-Tab, Zugriff: {website_url}")
            
            # ErstellenneuTab
            tab = await self.browser.get(website_url, new_tab=True)
            
            # WartenSeiteLadenAbgeschlossen
            page_loaded = False
            for retry in range(60):
                try:
                    await asyncio.sleep(1)
                    ready_state = await tab.evaluate("document.readyState")
                    if ready_state == "complete":
                        page_loaded = True
                        break
                except ConnectionRefusedError as e:
                    debug_logger.log_warning(f"[BrowserCaptcha] TabVerbindungVerloren: {e}")
                    return None
                except Exception as e:
                    debug_logger.log_warning(f"[BrowserCaptcha] WartenSeiteAusnahme: {e}, Retry {retry + 1}/60...")
                    await asyncio.sleep(1)
            
            if not page_loaded:
                debug_logger.log_error(f"[BrowserCaptcha] SeiteLadenTimeout (project: {project_id})")
                try:
                    await tab.close()
                except:
                    pass
                return None
            
            # Warten reCAPTCHA Laden
            recaptcha_ready = await self._wait_for_recaptcha(tab)
            
            if not recaptcha_ready:
                debug_logger.log_error(f"[BrowserCaptcha] reCAPTCHA LadenFehlgeschlagen (project: {project_id})")
                try:
                    await tab.close()
                except:
                    pass
                return None
            
            # ErstellenResidentInformationenObjekt
            resident_info = ResidentTabInfo(tab, project_id)
            resident_info.recaptcha_ready = True
            
            debug_logger.log_info(f"[BrowserCaptcha] ✅ Resident-TabErstellenErfolgreich (project: {project_id})")
            return resident_info
            
        except Exception as e:
            debug_logger.log_error(f"[BrowserCaptcha] ErstellenResident-TabAusnahme: {e}")
            return None

    async def _close_resident_tab(self, project_id: str):
        """SchliessenAngegeben project_id Resident-Tab
        
        Args:
            project_id: Projekt ID
        """
        resident_info = self._resident_tabs.pop(project_id, None)
        if resident_info and resident_info.tab:
            try:
                await resident_info.tab.close()
                debug_logger.log_info(f"[BrowserCaptcha] bereitsSchliessen project_id={project_id} Resident-Tab")
            except Exception as e:
                debug_logger.log_warning(f"[BrowserCaptcha] SchliessenTabbeiAusnahme: {e}")

    async def _get_token_legacy(self, project_id: str, action: str = "IMAGE_GENERATION") -> Optional[str]:
        """Traditioneller ModusAbrufen reCAPTCHA token(jedeMalErstellenneuTab)

        Args:
            project_id: FlowProjektID
            action: reCAPTCHA actionTyp (IMAGE_GENERATION Oder VIDEO_GENERATION)

        Returns:
            reCAPTCHA tokenString, wieErgebnisAbrufenFehlgeschlagenZurueckgebenNone
        """
        # SicherstellenBrowserbereitsStarten
        if not self._initialized or not self.browser:
            await self.initialize()

        start_time = time.time()
        tab = None

        try:
            website_url = f"https://labs.google/fx/tools/flow/project/{project_id}"
            debug_logger.log_info(f"[BrowserCaptcha] [Legacy] ZugriffSeite: {website_url}")

            # neuErstellenTabundZugriffSeite
            tab = await self.browser.get(website_url)

            # WartenSeiteAbgeschlossenalleLaden(ErhoehenWartenbeiZwischen)
            debug_logger.log_info("[BrowserCaptcha] [Legacy] WartenSeiteLaden...")
            await tab.sleep(3)
            
            # WartenSeite DOM Abgeschlossen
            for _ in range(10):
                ready_state = await tab.evaluate("document.readyState")
                if ready_state == "complete":
                    break
                await tab.sleep(0.5)

            # Warten reCAPTCHA Laden
            recaptcha_ready = await self._wait_for_recaptcha(tab)

            if not recaptcha_ready:
                debug_logger.log_error("[BrowserCaptcha] [Legacy] reCAPTCHA keinMethodeLaden")
                return None

            # Ausfuehren reCAPTCHA
            debug_logger.log_info(f"[BrowserCaptcha] [Legacy] Ausfuehren reCAPTCHA Validieren (action: {action})...")
            token = await self._execute_recaptcha_on_tab(tab, action)

            duration_ms = (time.time() - start_time) * 1000

            if token:
                self._last_fingerprint = await self._extract_tab_fingerprint(tab)
                debug_logger.log_info(f"[BrowserCaptcha] [Legacy] ✅ TokenAbrufenErfolgreich(Verbrauchenbei {duration_ms:.0f}ms)")
                return token
            else:
                debug_logger.log_error("[BrowserCaptcha] [Legacy] TokenAbrufenFehlgeschlagen(Zurueckgebennull)")
                return None

        except Exception as e:
            debug_logger.log_error(f"[BrowserCaptcha] [Legacy] AbrufentokenAusnahme: {str(e)}")
            return None
        finally:
            # SchliessenTab(aberBeibehaltenBrowser)
            if tab:
                try:
                    await tab.close()
                except Exception:
                    pass

    def get_last_fingerprint(self) -> Optional[Dict[str, Any]]:
        """ZurueckgebenAm meistenLetzteeinMalCaptcha-LoesungbeiBrowser-FingerabdruckSnapshot。"""
        if not self._last_fingerprint:
            return None
        return dict(self._last_fingerprint)

    async def close(self):
        """SchliessenBrowser"""
        # ZuerstStoppenallehatResident-Modus(SchliessenallehatResident-Tab)
        await self.stop_resident_mode()
        
        try:
            custom_items = list(self._custom_tabs.values())
            self._custom_tabs.clear()
            for item in custom_items:
                tab = item.get("tab") if isinstance(item, dict) else None
                if tab:
                    try:
                        await tab.close()
                    except Exception:
                        pass

            if self.browser:
                try:
                    self.browser.stop()
                except Exception as e:
                    debug_logger.log_warning(f"[BrowserCaptcha] SchliessenBrowserbeiAktuellAusnahme: {str(e)}")
                finally:
                    self.browser = None

            self._initialized = False
            self._resident_tabs.clear()  # SicherstellenBereinigenleerResidentWoerterbuch
            self._resident_error_streaks.clear()
            debug_logger.log_info("[BrowserCaptcha] BrowserbereitsSchliessen")
        except Exception as e:
            debug_logger.log_error(f"[BrowserCaptcha] SchliessenBrowserAusnahme: {str(e)}")

    async def open_login_window(self):
        """oeffnenAnmeldenFensterBereitstellenBenutzerManuellAnmelden Google"""
        await self.initialize()
        tab = await self.browser.get("https://accounts.google.com/")
        debug_logger.log_info("[BrowserCaptcha] BitteinoeffnenBrowserinAnmeldenKonto。AnmeldenAbgeschlossennach, keinbenoetigenSchliessenBrowser, SkriptunterMalAusfuehrenbeiwirdAutomatischVerwendendieseStatus。")
        print("BitteinoeffnenBrowserinAnmeldenKonto。AnmeldenAbgeschlossennach, keinbenoetigenSchliessenBrowser, SkriptunterMalAusfuehrenbeiwirdAutomatischVerwendendieseStatus。")

    # ========== Session Token Aktualisieren ==========

    async def refresh_session_token(self, project_id: str) -> Optional[str]:
        """vonResident-TabAbrufenAm meistenneu Session Token
        
        Wiederverwenden reCAPTCHA Resident-Tab, DurchAktualisierenSeiteundvon cookies inExtrahieren
        __Secure-next-auth.session-token
        
        Args:
            project_id: ProjektID, verwendenFuerBestimmenPositionResident-Tab
            
        Returns:
            neu Session Token, wieErgebnisAbrufenFehlgeschlagenZurueckgeben None
        """
        # SicherstellenBrowserbereitsInitialisieren
        await self.initialize()
        
        start_time = time.time()
        debug_logger.log_info(f"[BrowserCaptcha] oeffnenAnfangAktualisieren Session Token (project: {project_id})...")
        
        # VersuchenversuchenAbrufenOderErstellenResident-Tab
        async with self._resident_lock:
            resident_info = self._resident_tabs.get(project_id)
            
            # wieErgebnisdiese project_id KeinhatResident-Tab, dannErstellen
            if resident_info is None:
                debug_logger.log_info(f"[BrowserCaptcha] project_id={project_id} KeinhatResident-Tab, GeradeinErstellen...")
                resident_info = await self._create_resident_tab(project_id)
                if resident_info is None:
                    debug_logger.log_warning(f"[BrowserCaptcha] keinMethodefuer project_id={project_id} ErstellenResident-Tab")
                    return None
                self._resident_tabs[project_id] = resident_info
        
        if not resident_info or not resident_info.tab:
            debug_logger.log_error(f"[BrowserCaptcha] keinMethodeAbrufenResident-Tab")
            return None
        
        tab = resident_info.tab
        
        try:
            # AktualisierenSeitemitAbrufenAm meistenneu cookies
            debug_logger.log_info(f"[BrowserCaptcha] AktualisierenResident-TabmitAbrufenAm meistenneu cookies...")
            await tab.reload()
            
            # WartenSeiteLadenAbgeschlossen
            for i in range(30):
                await asyncio.sleep(1)
                try:
                    ready_state = await tab.evaluate("document.readyState")
                    if ready_state == "complete":
                        break
                except Exception:
                    pass
            
            # ZusaetzlichausserhalbWartenSicherstellen cookies bereitsSetzen
            await asyncio.sleep(2)
            
            # von cookies inExtrahieren __Secure-next-auth.session-token
            # nodriver kannmitDurch browser Abrufen cookies
            session_token = None
            
            try:
                # Verwenden nodriver  cookies API Abrufenallehat cookies
                cookies = await self.browser.cookies.get_all()
                
                for cookie in cookies:
                    if cookie.name == "__Secure-next-auth.session-token":
                        session_token = cookie.value
                        break
                        
            except Exception as e:
                debug_logger.log_warning(f"[BrowserCaptcha] Durch cookies API AbrufenFehlgeschlagen: {e}, Versuchenversuchenvon document.cookie Abrufen...")
                
                # AlternativeLoesung: Durch JavaScript Abrufen (Hinweis: HttpOnly cookies kannkannkeinMethodeDurchdieseFormatAbrufen)
                try:
                    all_cookies = await tab.evaluate("document.cookie")
                    if all_cookies:
                        for part in all_cookies.split(";"):
                            part = part.strip()
                            if part.startswith("__Secure-next-auth.session-token="):
                                session_token = part.split("=", 1)[1]
                                break
                except Exception as e2:
                    debug_logger.log_error(f"[BrowserCaptcha] document.cookie AbrufenFehlgeschlagen: {e2}")
            
            duration_ms = (time.time() - start_time) * 1000
            
            if session_token:
                debug_logger.log_info(f"[BrowserCaptcha] ✅ Session Token AbrufenErfolgreich(Verbrauchenbei {duration_ms:.0f}ms)")
                return session_token
            else:
                debug_logger.log_error(f"[BrowserCaptcha] ❌ nichtsuchenauf __Secure-next-auth.session-token cookie")
                return None
                
        except Exception as e:
            debug_logger.log_error(f"[BrowserCaptcha] Aktualisieren Session Token Ausnahme: {str(e)}")
            
            # Resident-TabkannkannbereitsUngueltig, VersuchenversuchenNeuerstellung
            async with self._resident_lock:
                await self._close_resident_tab(project_id)
                resident_info = await self._create_resident_tab(project_id)
                if resident_info:
                    self._resident_tabs[project_id] = resident_info
                    # NeuerstellungnachErneutMalVersuchenversuchenAbrufen
                    try:
                        cookies = await self.browser.cookies.get_all()
                        for cookie in cookies:
                            if cookie.name == "__Secure-next-auth.session-token":
                                debug_logger.log_info(f"[BrowserCaptcha] ✅ Neuerstellungnach Session Token AbrufenErfolgreich")
                                return cookie.value
                    except Exception:
                        pass
            
            return None

    # ========== Statusabfrage ==========

    def is_resident_mode_active(self) -> bool:
        """PruefenistObhatWelcheResident-TabAktivieren"""
        return len(self._resident_tabs) > 0 or self._running

    def get_resident_count(self) -> int:
        """AbrufenwennvorResident-TabAnzahlMenge"""
        return len(self._resident_tabs)

    def get_resident_project_ids(self) -> list[str]:
        """AbrufenallehatwennvorResident project_id Liste"""
        return list(self._resident_tabs.keys())

    def get_resident_project_id(self) -> Optional[str]:
        """AbrufenwennvorResident project_id(RichtungnachKompatibel, ZurueckgebenErsteStueck)"""
        if self._resident_tabs:
            return next(iter(self._resident_tabs.keys()))
        return self.resident_project_id

    async def get_custom_token(
        self,
        website_url: str,
        website_key: str,
        action: str = "homepage",
        enterprise: bool = False,
    ) -> Optional[str]:
        """fuerBeliebigSeiteAusfuehren reCAPTCHA, verwendenFuerAnzahlTestSzenario。

        mitNormal legacy ModusnichtGleich, HierwirdWiederverwendenGleichStueckResident-Tab, VermeidenjedeMalKaltStartenneu tab。
        """
        await self.initialize()
        self._last_fingerprint = None

        cache_key = f"{website_url}|{website_key}|{1 if enterprise else 0}"
        warmup_seconds = float(getattr(config, "browser_score_test_warmup_seconds", 12) or 12)
        per_request_settle_seconds = float(
            getattr(config, "browser_score_test_settle_seconds", 2.5) or 2.5
        )
        max_retries = 2

        async with self._custom_lock:
            for attempt in range(max_retries):
                start_time = time.time()
                custom_info = self._custom_tabs.get(cache_key)
                tab = custom_info.get("tab") if isinstance(custom_info, dict) else None

                try:
                    if tab is None:
                        debug_logger.log_info(f"[BrowserCaptcha] [Custom] ErstellenResidentTestTab: {website_url}")
                        tab = await self.browser.get(website_url, new_tab=True)
                        custom_info = {
                            "tab": tab,
                            "recaptcha_ready": False,
                            "warmed_up": False,
                            "created_at": time.time(),
                        }
                        self._custom_tabs[cache_key] = custom_info

                    page_loaded = False
                    for _ in range(20):
                        ready_state = await tab.evaluate("document.readyState")
                        if ready_state == "complete":
                            page_loaded = True
                            break
                        await tab.sleep(0.5)

                    if not page_loaded:
                        raise RuntimeError("DefinitionSeiteLadenTimeout")

                    if not custom_info.get("recaptcha_ready"):
                        recaptcha_ready = await self._wait_for_custom_recaptcha(
                            tab=tab,
                            website_key=website_key,
                            enterprise=enterprise,
                        )
                        if not recaptcha_ready:
                            raise RuntimeError("Definition reCAPTCHA keinMethodeLaden")
                        custom_info["recaptcha_ready"] = True

                    try:
                        await tab.evaluate("""
                            (() => {
                                try {
                                    const body = document.body || document.documentElement;
                                    const width = window.innerWidth || 1280;
                                    const height = window.innerHeight || 720;
                                    const x = Math.max(24, Math.floor(width * 0.38));
                                    const y = Math.max(24, Math.floor(height * 0.32));
                                    const moveEvent = new MouseEvent('mousemove', {
                                        bubbles: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    const overEvent = new MouseEvent('mouseover', {
                                        bubbles: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    window.focus();
                                    window.dispatchEvent(new Event('focus'));
                                    document.dispatchEvent(moveEvent);
                                    document.dispatchEvent(overEvent);
                                    if (body) {
                                        body.dispatchEvent(moveEvent);
                                        body.dispatchEvent(overEvent);
                                    }
                                    window.scrollTo(0, Math.min(320, document.body?.scrollHeight || 320));
                                } catch (e) {}
                            })()
                        """)
                    except Exception:
                        pass

                    if not custom_info.get("warmed_up"):
                        if warmup_seconds > 0:
                            debug_logger.log_info(
                                f"[BrowserCaptcha] [Custom] ErsteMalAufwaermenTestSeite {warmup_seconds:.1f}s nachErneutAusfuehren token"
                            )
                            try:
                                await tab.evaluate("""
                                    (() => {
                                        try {
                                            window.scrollTo(0, Math.min(240, document.body.scrollHeight || 240));
                                            window.dispatchEvent(new Event('mousemove'));
                                            window.dispatchEvent(new Event('focus'));
                                        } catch (e) {}
                                    })()
                                """)
                            except Exception:
                                pass
                            await tab.sleep(warmup_seconds)
                        custom_info["warmed_up"] = True
                    elif per_request_settle_seconds > 0:
                        debug_logger.log_info(
                            f"[BrowserCaptcha] [Custom] WiederverwendenTestTab, AusfuehrenvorZusaetzlichausserhalbWarten {per_request_settle_seconds:.1f}s"
                        )
                        await tab.sleep(per_request_settle_seconds)

                    debug_logger.log_info(f"[BrowserCaptcha] [Custom] VerwendenResidentTestTabAusfuehrenValidieren (action: {action})...")
                    token = await self._execute_custom_recaptcha_on_tab(
                        tab=tab,
                        website_key=website_key,
                        action=action,
                        enterprise=enterprise,
                    )

                    duration_ms = (time.time() - start_time) * 1000
                    if token:
                        extracted_fingerprint = await self._extract_tab_fingerprint(tab)
                        if not extracted_fingerprint:
                            try:
                                fallback_ua = await tab.evaluate("navigator.userAgent || ''")
                                fallback_lang = await tab.evaluate("navigator.language || ''")
                                extracted_fingerprint = {
                                    "user_agent": fallback_ua or "",
                                    "accept_language": fallback_lang or "",
                                    "proxy_url": None,
                                }
                            except Exception:
                                extracted_fingerprint = None
                        self._last_fingerprint = extracted_fingerprint
                        debug_logger.log_info(
                            f"[BrowserCaptcha] [Custom] ✅ ResidentTestTab TokenAbrufenErfolgreich(Verbrauchenbei {duration_ms:.0f}ms)"
                        )
                        return token

                    raise RuntimeError("Definition token AbrufenFehlgeschlagen(Zurueckgeben null)")
                except Exception as e:
                    debug_logger.log_warning(
                        f"[BrowserCaptcha] [Custom] Versuchenversuchen {attempt + 1}/{max_retries} Fehlgeschlagen: {str(e)}"
                    )
                    stale_info = self._custom_tabs.pop(cache_key, None)
                    stale_tab = stale_info.get("tab") if isinstance(stale_info, dict) else None
                    if stale_tab:
                        try:
                            await stale_tab.close()
                        except Exception:
                            pass
                    if attempt >= max_retries - 1:
                        debug_logger.log_error(f"[BrowserCaptcha] [Custom] AbrufentokenAusnahme: {str(e)}")
                        return None

            return None

    async def get_custom_score(
        self,
        website_url: str,
        website_key: str,
        verify_url: str,
        action: str = "homepage",
        enterprise: bool = False,
    ) -> Dict[str, Any]:
        """inGleichStueckResident-TabinAbrufen token undDirektValidierungSeiteAnzahl。"""
        token_started_at = time.time()
        token = await self.get_custom_token(
            website_url=website_url,
            website_key=website_key,
            action=action,
            enterprise=enterprise,
        )
        token_elapsed_ms = int((time.time() - token_started_at) * 1000)

        if not token:
            return {
                "token": None,
                "token_elapsed_ms": token_elapsed_ms,
                "verify_mode": "browser_page",
                "verify_elapsed_ms": 0,
                "verify_http_status": None,
                "verify_result": {},
            }

        cache_key = f"{website_url}|{website_key}|{1 if enterprise else 0}"
        async with self._custom_lock:
            custom_info = self._custom_tabs.get(cache_key)
            tab = custom_info.get("tab") if isinstance(custom_info, dict) else None
            if tab is None:
                raise RuntimeError("SeiteAnzahlTestTabnichtspeichernin")
            verify_payload = await self._verify_score_on_tab(tab, token, verify_url)

        return {
            "token": token,
            "token_elapsed_ms": token_elapsed_ms,
            **verify_payload,
        }
