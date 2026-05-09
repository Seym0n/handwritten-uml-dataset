import subprocess
import threading
import atexit
import os

class PlantUMLServer:
    """
    Persistent PlantUML process for fast XMI generation.
    Reuses a single Java process to avoid JVM startup overhead.
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        # Use absolute path to JAR file (same directory as this script)
        # Try custom JAR with pipe error handling (custompip3) first, fallback to standard
        custom_jar = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantuml-custompipe-v3.jar")
        standard_jar = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantuml-mit-1.2026.0.jar")

        if os.path.exists(custom_jar):
            jar_path = custom_jar
            print(f"Using custom PlantUML JAR with persistent pipe error handling")
        else:
            jar_path = standard_jar
            print(f"Using standard PlantUML JAR (will restart on errors)")

        self.process = subprocess.Popen(
            ["java", "-jar", jar_path, "-pipe", "-xmi:star"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=0
        )
        atexit.register(self.close)
    
    def plantuml_to_xmi(self, plantuml_code):
        """
        Convert PlantUML code to XMI format using persistent process.
        
        Args:
            plantuml_code (str): PlantUML diagram code
        
        Returns:
            str: XMI output, or None if generation failed
        """
        with self.lock:
            try:
                # Ensure proper PlantUML format
                # Count @startuml and @enduml tags to handle sequential diagrams
                startuml_count = plantuml_code.count('@startuml')
                enduml_count = plantuml_code.count('@enduml')

                if startuml_count == 0:
                    # No diagrams: wrap entire code
                    plantuml_code = '@startuml\n' + plantuml_code + '\n@enduml'
                elif startuml_count > enduml_count:
                    # More starts than ends: add missing @enduml tags
                    missing_ends = startuml_count - enduml_count
                    plantuml_code = plantuml_code + ('\n@enduml' * missing_ends)

                # Send input to PlantUML process
                self.process.stdin.write(plantuml_code.encode('utf-8'))
                self.process.stdin.write(b'\n')
                self.process.stdin.flush()
                
                # Read output until closing XMI tag
                output = []
                while True:
                    line = self.process.stdout.readline().decode('utf-8')
                    if not line:
                        break
                    
                    output.append(line)
                    
                    if '</XMI>' in line:
                        break
                
                result = ''.join(output)

                # Check if output is error XMI (from custompip3.jar)
                if '<XMI.exporterVersion>ERROR</XMI.exporterVersion>' in result:
                    # Invalid PlantUML, but process survived (no restart needed)
                    return None

                # Check if output is valid
                if not result or not result.strip().startswith('<?xml'):
                    print("Warning: Invalid PlantUML code, restarting process")
                    self.close()
                    self.__init__()  # Restart process
                    return None

                return result
                
            except Exception as e:
                print(f"Error: {e}, restarting process")
                self.close()
                self.__init__()
                return None
    
    def close(self):
        """Terminate the PlantUML process"""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()


# Global server instance (singleton pattern)
_plantuml_server = None

def _extract_plantuml_code(code):
    """
    Extract PlantUML code from various input formats.

    Handles:
    - Markdown code fences: ```plantuml\n@startuml\n...\n@enduml\n```
    - Raw PlantUML with tags: @startuml\n...\n@enduml
    - PlantUML without tags: class A (will add tags automatically)
    - Extra text before/after PlantUML (extracts content between @startuml and @enduml)

    Args:
        code (str): Input code in any format

    Returns:
        str: Clean PlantUML code
    """
    import re

    code = code.strip()

    # First, remove markdown code fences if present
    if code.startswith('```'):
        lines = code.split('\n')
        # Remove first line (```plantuml or ```)
        lines = lines[1:]
        # Remove last line if it's a closing fence
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        code = '\n'.join(lines).strip()

    # Extract content between @startuml and @enduml (most robust approach)
    # This handles cases where there's extra text before/after
    match = re.search(r'@startuml.*?@enduml', code, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)

    # If no @startuml/@enduml tags found, return as-is
    # (the PlantUMLServer will add them automatically)
    return code

def plantuml_to_xmi(plantuml_code):
    """
    Module-level wrapper for PlantUML to XMI conversion using singleton server.

    Automatically handles various input formats:
    - Raw PlantUML: "@startuml\nclass A\n@enduml"
    - Markdown-wrapped: "```plantuml\n@startuml\nclass A\n@enduml\n```"
    - With extra text: "Here's my diagram:\n@startuml\nclass A\n@enduml\nThanks!"
    - Without tags: "class A" (tags added automatically)

    Args:
        plantuml_code (str): PlantUML diagram code in any format

    Returns:
        str: XMI output, or None if generation failed
    """
    global _plantuml_server
    if _plantuml_server is None:
        _plantuml_server = PlantUMLServer()

    # Extract clean PlantUML code
    clean_code = _extract_plantuml_code(plantuml_code)

    return _plantuml_server.plantuml_to_xmi(clean_code)

