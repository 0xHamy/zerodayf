from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
import asyncio
import threading
from pathlib import Path
from app.proxy.inspectors.route_inspector import RouteInspector


class EmbeddedMitm:
    def __init__(self, log_memory: list,
                 listen_host: str = "0.0.0.0", listen_port: int = 8080,
                 mode: str = None, upstream_cert: bool = True):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.mode = mode
        self.upstream_cert = upstream_cert

        self.opts = options.Options(
            listen_host=self.listen_host,
            listen_port=self.listen_port,
            http2=True, 
            ssl_insecure=True
        )
        if self.mode:
            self.opts.mode = self.mode
        if not self.upstream_cert:
            self.opts.upstream_cert = False

        self.dump_master = DumpMaster(self.opts, with_termlog=False, with_dumper=False)
        
        # Always use RouteInspector
        self.inspector = RouteInspector(log_memory)
        self.dump_master.addons.add(self.inspector)

        self.is_running = False
        self._thread = None
        self._shutdown_event = threading.Event()

    async def start(self):
        if self.is_running:
            print("Mitmproxy is already running.")
            return
        
        try:
            # Clear any previous shutdown signal
            self._shutdown_event.clear()
            self.is_running = True
            print(f"Starting mitmproxy on {self.listen_host}:{self.listen_port} (mode={self.mode})...")
            
            # Start mitmproxy in a separate thread
            self._thread = threading.Thread(target=self._run_in_thread)
            self._thread.daemon = True  # Make thread exit when main program exits
            self._thread.start()
            
            # Give the thread a moment to start up
            await asyncio.sleep(0.1)
            
        except Exception as e:
            self.is_running = False
            print(f"Error starting mitmproxy: {e}")
            raise

    def _run_in_thread(self):
        """Run mitmproxy in a separate thread with its own event loop"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run mitmproxy in this thread's event loop
            loop.run_until_complete(self._run_mitmproxy())
        except Exception as e:
            print(f"Thread error in mitmproxy: {e}")
        finally:
            loop.close()
            self.is_running = False

    async def _run_mitmproxy(self):
        """Wrapper around mitmproxy's run method to handle potential exits"""
        try:
            # Create a task for running mitmproxy
            proxy_task = asyncio.create_task(self.dump_master.run())
            
            # Create a task for monitoring the shutdown event
            shutdown_check_task = asyncio.create_task(self._monitor_shutdown())
            
            # Wait for either the proxy to finish or a shutdown signal
            done, pending = await asyncio.wait(
                [proxy_task, shutdown_check_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                
            # Handle the completed task
            for task in done:
                if task == proxy_task and not task.cancelled():
                    # Proxy finished normally
                    await task
                    
        except SystemExit as e:
            print(f"Mitmproxy exited with code: {e.code}")
            # We don't re-raise here since we're in a separate thread
        except Exception as e:
            print(f"Unexpected error in mitmproxy: {e}")
        finally:
            self.is_running = False

    async def _monitor_shutdown(self):
        """Monitor for shutdown event from another thread"""
        while not self._shutdown_event.is_set():
            # Check the shutdown event periodically
            await asyncio.sleep(0.1)
        
        # If we get here, shutdown was requested
        self.dump_master.shutdown()

    async def stop(self):
        if not self.is_running:
            print("Mitmproxy is not running.")
            return
        
        try:
            print("Shutting down mitmproxy...")
            
            # Signal the thread to shut down
            self._shutdown_event.set()
            
            # Wait for the thread to complete (with timeout)
            if self._thread and self._thread.is_alive():
                # Give up to 5 seconds for clean shutdown
                for _ in range(50):  # 5 seconds (50 * 0.1)
                    if not self.is_running or not self._thread.is_alive():
                        break
                    await asyncio.sleep(0.1)
                
                # If still running after timeout, we consider it stopped anyway
                # The daemon thread will be terminated when the program exits
            
            self.is_running = False
            self._thread = None
            print("Mitmproxy stopped.")
            
        except Exception as e:
            self.is_running = False
            print(f"Error during mitmproxy shutdown: {e}")
            raise
