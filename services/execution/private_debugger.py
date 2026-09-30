import sys
import traceback
import linecache
import functools

class PrivatePythonDebugger:
    """
    A personal and privately owned Python debugger. 
    Enforces local inspection, secure runtime tracking, and precise step execution 
    aligned with institutional rigor and utility-first principles.
    """

    def __init__(self):
        self.breakpoints = {}
        self.history = []
        self.is_active = True

    def set_breakpoint(self, filename, lineno):
        """Sets an internal checkpoint for execution tracing."""
        if filename not in self.breakpoints:
            self.breakpoints[filename] = set()
        self.breakpoints[filename].add(lineno)
        print(f"[DEBUGGER] Breakpoint registered at {filename}:{lineno}")

    def _inspect_frame(self, frame):
        """Extracts local variables and state metrics safely."""
        code = frame.f_code
        filename = code.co_filename
        lineno = frame.f_lineno
        func_name = code.co_name
        
        line = linecache.getline(filename, lineno).strip()
        
        print("\n=======================================")
        print(f"   PRIVATE DEBUGGER INTERRUPT")
        print(f"=======================================")
        print(f"File: {filename}")
        print(f"Function: {func_name} | Line: {lineno}")
        print(f"Code: {line}")
        print("---------------------------------------")
        print("Local Variables:")
        for key, val in frame.f_locals.items():
            print(f"  {key} = {val!r}")
        print("=======================================")

    def trace_handler(self, frame, event, arg):
        """Core trace function hook for Python's sys.settrace."""
        if not self.is_active:
            return None

        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        if event == 'call':
            # Track function calls if needed
            pass

        elif event == 'line':
            # Check if current line has a registered breakpoint
            if filename in self.breakpoints and lineno in self.breakpoints[filename]:
                self._inspect_frame(frame)
                self.interactive_prompt(frame)

        return self.trace_handler

    def interactive_prompt(self, frame):
        """CLI interactive loop for inspecting code state during execution."""
        while True:
            command = input("debug> ").strip()
            
            if command == 'continue' or command == 'c':
                print("[DEBUGGER] Resuming execution...")
                break
            elif command == 'quit' or command == 'q':
                print("[DEBUGGER] Terminating execution session.")
                self.is_active = False
                sys.exit(0)
            elif command.startswith('print ') or command.startswith('p '):
                expr = command.split(' ', 1)[1]
                try:
                    result = eval(expr, frame.f_globals, frame.f_locals)
                    print(f"{result}")
                except Exception as e:
                    print(f"Error evaluating expression: {e}")
            elif command == 'locals':
                for k, v in frame.f_locals.items():
                    print(f"  {k}: {v}")
            elif command == 'help':
                print("Commands: continue (c), print <expr> (p), locals, quit (q)")
            else:
                print(f"Unknown command: '{command}'. Type 'help' for options.")

    def run_script(self, target_function, *args, **kwargs):
        """Runs a target function inside the debugger tracking scope."""
        original_trace = sys.gettrace()
        sys.settrace(self.trace_handler)
        
        result = None
        try:
            result = target_function(*args, **kwargs)
        except Exception as e:
            print(f"\n[DEBUGGER EXCEPTION TRAP]: {e}")
            traceback.print_exc()
        finally:
            sys.settrace(original_trace)
            
        return result

# ==========================================
# Example Usage Scenarios
# ==========================================
if __name__ == "__main__":
    debugger = PrivatePythonDebugger()

    # Define a sample function to debug
    def sample_compliance_verification(data_packet_id, risk_score):
        print(f"Processing data packet: {data_packet_id}")
        threshold = 50
        status = "Approved"
        
        # Artificial computation block
        if risk_score > threshold:
            status = "Flagged for Audit"
            
        return {"packet": data_packet_id, "risk": risk_score, "result": status}

    # Register a manual breakpoint targeting line numbers in sample function
    # (Note: Line numbers can be checked dynamically or pre-set)
    import inspect
    lines = inspect.getsourcelines(sample_compliance_verification)
    target_lineno = inspect.findsource(sample_compliance_verification)[1] + 4 # Target the risk check line
    
    debugger.set_breakpoint(__file__, target_lineno)

    print("--- STARTING PRIVATE DEBUGGER RUN ---")
    output = debugger.run_script(sample_compliance_verification, data_packet_id="SEC-9921", risk_score=75)
    print(f"Execution Output: {output}")
