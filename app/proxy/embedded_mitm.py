from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
import asyncio
from pathlib import Path


class EmbeddedMitm:
    """
    Embeds mitmproxy's DumpMaster so we can start/stop it from within FastAPI.
    Supports different inspector classes based on the framework.
    """

    def __init__(self, app_root: Path, log_memory: list,
                 listen_host: str = "0.0.0.0", listen_port: int = 8080,
                 mode: str = None, upstream_cert: bool = True,
                 inspector_class=None):
        """
        :param app_root: Path to code root for analyzing routes (Path object)
        :param log_memory: Shared list for storing log lines
        :param listen_host: IP to bind
        :param listen_port: Port for the proxy
        :param mode: e.g., "upstream:http://127.0.0.1:8888"
        :param upstream_cert: Whether to check upstream cert
        :param inspector_class: The inspector class to use
        """
        self.app_root = app_root
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.mode = mode
        self.upstream_cert = upstream_cert

        self.opts = options.Options(
            listen_host=self.listen_host,
            listen_port=self.listen_port,
            http2=True, 
        )
        if self.mode:
            self.opts.mode = self.mode
        if not self.upstream_cert:
            self.opts.upstream_cert = False

        self.dump_master = DumpMaster(self.opts, with_termlog=False, with_dumper=False)
        if inspector_class:
            self.inspector = inspector_class(self.app_root, log_memory)
            self.dump_master.addons.add(self.inspector)

        self.is_running = False
        self._task = None


    async def start(self):
        if self.is_running:
            print("Mitmproxy is already running.")
            return
        self.is_running = True
        print(f"Starting mitmproxy on {self.listen_host}:{self.listen_port} (mode={self.mode})...")

        self._task = asyncio.create_task(self.dump_master.run())


    async def stop(self):
        if not self.is_running:
            print("Mitmproxy is not running.")
            return
        print("Shutting down mitmproxy...")
        self.is_running = False
        self.dump_master.shutdown()

        if self._task:
            await self._task
        self._task = None
        print("Mitmproxy stopped.")
