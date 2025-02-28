from concurrent.futures import ThreadPoolExecutor
import asyncio, subprocess, json
from fastapi import HTTPException
from typing import Dict, Any, Union, List


async def scan_code_with_semgrep(codes_and_paths: List[Dict[str, str]], rules: Union[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    An asyncio function that uses Semgrep to scan multiple code snippets via stdin and returns simplified results as JSON.
    Each entry in codes_and_paths must have 'code' and 'path' keys.
    """
    try:
        # Construct the base Semgrep command
        if isinstance(rules, list):
            config_args = []
            for rule in rules:
                config_args.extend(["--config", rule])
        else:
            config_args = ["--config", rules]
        base_cmd = ["semgrep", *config_args, "--json", "-"]

        # Define a function to run Semgrep for a single code snippet in a separate thread
        def run_semgrep(code: str):
            process = subprocess.Popen(
                base_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(code.encode('utf-8'))
            return stdout, stderr, process.returncode

        # Process each code snippet individually
        async def process_single_code(entry: Dict[str, str]) -> List[Dict[str, Any]]:
            code = entry["code"]
            path = entry["path"]
            with ThreadPoolExecutor() as executor:
                stdout, stderr, returncode = await asyncio.get_event_loop().run_in_executor(
                    executor, lambda: run_semgrep(code)
                )
            
            if stdout:
                try:
                    full_results = json.loads(stdout.decode('utf-8'))
                    # Simplify results for this code snippet
                    simplified_results = []
                    for result in full_results.get("results", []):
                        simplified_result = {
                            "path": path,  # Use provided path
                            "code": code.strip(),  # Include the original code, stripped for cleanliness
                            "severity": result.get("extra", {}).get("severity", ""),
                            "impact": result.get("extra", {}).get("metadata", {}).get("impact", ""),
                            "message": result.get("extra", {}).get("message", ""),
                            "cwe": result.get("extra", {}).get("metadata", {}).get("cwe", [])
                        }
                        simplified_results.append(simplified_result)
                    # If no results, still include an entry to indicate the scan ran
                    if not simplified_results:
                        simplified_results.append({
                            "path": path,
                            "code": code.strip(),
                            "severity": "",
                            "impact": "",
                            "message": "No issues detected",
                            "cwe": []
                        })
                    return simplified_results
                except json.JSONDecodeError:
                    return [{"path": path, "code": code.strip(), "error": f"Failed to parse Semgrep output"}]
            else:
                stderr_text = stderr.decode('utf-8') if stderr else "No error message provided"
                return [{"path": path, "code": code.strip(), "error": f"Semgrep failed: {stderr_text}"}]

        # Run all scans concurrently and collect results
        tasks = [process_single_code(entry) for entry in codes_and_paths]
        results_per_code = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine all results into a single list
        combined_results = []
        for result in results_per_code:
            if isinstance(result, list):
                combined_results.extend(result)  # Extend with the list of results for this code
            elif isinstance(result, Exception):
                # Handle exceptions from individual tasks
                combined_results.append({"path": "unknown", "code": "unknown", "error": str(result)})

        return {"results": combined_results}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error running Semgrep scans: {str(e)}")


if __name__ == "__main__":
    codes_and_paths = [
        {
            "code": """
            @admin_bp.route("/blog")
            @login_required
            def blog():
                blogs = Blog.query.order_by(Blog.date.asc()).all()
                return render_template(
                    "manage_blog.html",
                    title="Manage Blogs",
                    user=current_user,
                    blogs=blogs
                )
            """,
            "path": "/app/backend/views.py#14-20"
        },
        {
            "code": """
            print("Hello")
            exec(input("Enter something else: "))
            """,
            "path": "/app/backend/utils.py#30-35"
        }
    ]
    rules = "p/security-audit"

    async def main():
        try:
            result = await scan_code_with_semgrep(codes_and_paths, rules)
            print("Simplified Semgrep Scan Results:")
            print(json.dumps(result, indent=2))
        except HTTPException as e:
            print(f"Error: {e.detail}")

    # Run the async function
    asyncio.run(main())
