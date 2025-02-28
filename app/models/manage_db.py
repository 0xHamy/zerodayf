import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import create_tables, empty_tables, CodeMappings, SessionLocal, CodeScans

async def populate_dummy_code_mappings():
    """
    Populate the code_mappings table with dummy data using async session.
    """
    dummy_data = [
        {
            "endpoint": "/edit/file/1",
            "code_file_paths": "/app/backend/views.py#41-59,/app/frontend/templates/edit.html#1-100"
        },
        {
            "endpoint": "/api/users/profile",
            "code_file_paths": "/app/backend/api/user_views.py#15-45,/app/frontend/components/Profile.jsx#10-150"
        },
        {
            "endpoint": "/dashboard/analytics",
            "code_file_paths": "/app/backend/services/analytics.py#100-180,/app/frontend/views/Dashboard.vue#25-200"
        },
        {
            "endpoint": "/auth/login",
            "code_file_paths": "/app/backend/auth/views.py#20-89,/app/frontend/pages/Login.tsx#1-120,/app/backend/services/auth.py#50-75"
        },
        {
            "endpoint": "/projects/create",
            "code_file_paths": "/app/backend/projects/views.py#30-150,/app/frontend/components/ProjectForm.jsx#5-250,/app/backend/models/project.py#10-40"
        }
    ]
    
    async with SessionLocal() as session:
        for data in dummy_data:
            mapping = CodeMappings(
                endpoint=data["endpoint"],
                code_file_paths=data["code_file_paths"]
            )
            session.add(mapping)
        
        try:
            await session.commit()
            print("Successfully added dummy code mappings")
        except Exception as e:
            await session.rollback()
            print(f"Error adding dummy data: {str(e)}")


async def populate_dummy_code_scans():
    """
    Populate the code_scans table with dummy data using async session.
    """
    dummy_data = [
        {
            "scan_name": "ProjectA_Security_Scan",
            "uid": "semgrep_001",
            "scan_type": "semgrep",
            "scan_template": "rules/semgrep/security.yaml",
            "scan_result": """[{"path":"/app/backend/views.py#93-180","result":{"version":"1.109.0","scanned_code":"eval(input)","results":[{"check_id":"python.lang.security.audit.eval-detected.eval-detected","path":"/tmp/tmpj962l4j_/stdin","start":{"line":1,"col":1,"offset":0},"end":{"line":1,"col":12,"offset":11},"extra":{"message":"Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.","metadata":{"source-rule-url":"https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval","cwe":["CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')"],"owasp":["A03:2021 - Injection"],"asvs":{"control_id":"5.2.4 Dyanmic Code Execution Features","control_url":"https://github.com/OWASP/ASVS/blob/master/4.0/en/0x13-V5-Validation-Sanitization-Encoding.md#v52-sanitization-and-sandboxing-requirements","section":"V5: Validation, Sanitization and Encoding Verification Requirements","version":"4"},"category":"security","technology":["python"],"references":["https://owasp.org/Top10/A03_2021-Injection"],"subcategory":["audit"],"likelihood":"LOW","impact":"HIGH","confidence":"LOW","license":"Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license","vulnerability_class":["Code Injection"],"source":"https://semgrep.dev/r/python.lang.security.audit.eval-detected.eval-detected","shortlink":"https://sg.run/ZvrD"},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}}],"errors":[{"code":2,"level":"warn","type":"Other syntax error","message":"Other syntax error at line /tmp/tmpj962l4j_/stdin:1:\n Failure: not a program","path":"/tmp/tmpj962l4j_/stdin"}],"paths":{"scanned":["/tmp/tmpj962l4j_/stdin"]},"skipped_rules":[]}},{"path":"/app/frontend/template.html#89-110","result":{"version":"1.109.0","scanned_code":"eval(input)","results":[{"check_id":"python.lang.security.audit.eval-detected.eval-detected","path":"/tmp/tmpj962l4j_/stdin","start":{"line":1,"col":1,"offset":0},"end":{"line":1,"col":12,"offset":11},"extra":{"message":"Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.","metadata":{"source-rule-url":"https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval","cwe":["CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')"],"owasp":["A03:2021 - Injection"],"asvs":{"control_id":"5.2.4 Dyanmic Code Execution Features","control_url":"https://github.com/OWASP/ASVS/blob/master/4.0/en/0x13-V5-Validation-Sanitization-Encoding.md#v52-sanitization-and-sandboxing-requirements","section":"V5: Validation, Sanitization and Encoding Verification Requirements","version":"4"},"category":"security","technology":["python"],"references":["https://owasp.org/Top10/A03_2021-Injection"],"subcategory":["audit"],"likelihood":"LOW","impact":"HIGH","confidence":"LOW","license":"Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license","vulnerability_class":["Code Injection"],"source":"https://semgrep.dev/r/python.lang.security.audit.eval-detected.eval-detected","shortlink":"https://sg.run/ZvrD"},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}}],"errors":[{"code":2,"level":"warn","type":"Other syntax error","message":"Other syntax error at line /tmp/tmpj962l4j_/stdin:1:\n Failure: not a program","path":"/tmp/tmpj962l4j_/stdin"}],"paths":{"scanned":["/tmp/tmpj962l4j_/stdin"]},"skipped_rules":[]}}]"""
        },
        {
            "scan_name": "UserAPI_Performance_Scan",
            "uid": "ai_001",
            "scan_type": "ai",
            "scan_template": "templates/ai/performance_check.json",
            "scan_result": """# Performance Scan Results\n\n## Issues\n- **Slow Query**: `user_views.py:30` takes 500ms. Consider indexing.\n- **High Memory Usage**: `Profile.jsx:50` loads large datasets."""
        },
        {
            "scan_name": "Analytics_Module_Scan",
            "uid": "semgrep_002",
            "scan_type": "semgrep",
            "scan_template": "rules/semgrep/code_quality.yaml",
            "scan_result": """[{"path":"/app/backend/views.py#93-180","result":{"version":"1.109.0","scanned_code":"eval(input)","results":[{"check_id":"python.lang.security.audit.eval-detected.eval-detected","path":"/tmp/tmpj962l4j_/stdin","start":{"line":1,"col":1,"offset":0},"end":{"line":1,"col":12,"offset":11},"extra":{"message":"Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.","metadata":{"source-rule-url":"https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval","cwe":["CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')"],"owasp":["A03:2021 - Injection"],"asvs":{"control_id":"5.2.4 Dyanmic Code Execution Features","control_url":"https://github.com/OWASP/ASVS/blob/master/4.0/en/0x13-V5-Validation-Sanitization-Encoding.md#v52-sanitization-and-sandboxing-requirements","section":"V5: Validation, Sanitization and Encoding Verification Requirements","version":"4"},"category":"security","technology":["python"],"references":["https://owasp.org/Top10/A03_2021-Injection"],"subcategory":["audit"],"likelihood":"LOW","impact":"HIGH","confidence":"LOW","license":"Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license","vulnerability_class":["Code Injection"],"source":"https://semgrep.dev/r/python.lang.security.audit.eval-detected.eval-detected","shortlink":"https://sg.run/ZvrD"},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}}],"errors":[{"code":2,"level":"warn","type":"Other syntax error","message":"Other syntax error at line /tmp/tmpj962l4j_/stdin:1:\n Failure: not a program","path":"/tmp/tmpj962l4j_/stdin"}],"paths":{"scanned":["/tmp/tmpj962l4j_/stdin"]},"skipped_rules":[]}},{"path":"/app/frontend/template.html#89-110","result":{"version":"1.109.0","scanned_code":"eval(input)","results":[{"check_id":"python.lang.security.audit.eval-detected.eval-detected","path":"/tmp/tmpj962l4j_/stdin","start":{"line":1,"col":1,"offset":0},"end":{"line":1,"col":12,"offset":11},"extra":{"message":"Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.","metadata":{"source-rule-url":"https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval","cwe":["CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')"],"owasp":["A03:2021 - Injection"],"asvs":{"control_id":"5.2.4 Dyanmic Code Execution Features","control_url":"https://github.com/OWASP/ASVS/blob/master/4.0/en/0x13-V5-Validation-Sanitization-Encoding.md#v52-sanitization-and-sandboxing-requirements","section":"V5: Validation, Sanitization and Encoding Verification Requirements","version":"4"},"category":"security","technology":["python"],"references":["https://owasp.org/Top10/A03_2021-Injection"],"subcategory":["audit"],"likelihood":"LOW","impact":"HIGH","confidence":"LOW","license":"Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license","vulnerability_class":["Code Injection"],"source":"https://semgrep.dev/r/python.lang.security.audit.eval-detected.eval-detected","shortlink":"https://sg.run/ZvrD"},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}}],"errors":[{"code":2,"level":"warn","type":"Other syntax error","message":"Other syntax error at line /tmp/tmpj962l4j_/stdin:1:\n Failure: not a program","path":"/tmp/tmpj962l4j_/stdin"}],"paths":{"scanned":["/tmp/tmpj962l4j_/stdin"]},"skipped_rules":[]}}]"""
        },
        {
            "scan_name": "Login_Auth_Scan",
            "uid": "ai_002",
            "scan_type": "ai",
            "scan_template": "templates/ai/auth_analysis.json",
            "scan_result": """# Authentication Scan\n\n## Results\n- **Weak Password Hash**: `auth.py:60` uses MD5. Upgrade to bcrypt.\n- **CSRF Missing**: `Login.tsx:90` lacks token."""
        }
    ]
    
    async with SessionLocal() as session:
        for data in dummy_data:
            scan = CodeScans(
                scan_name=data["scan_name"],
                uid=data["uid"],
                scan_type=data["scan_type"],
                scan_template=data["scan_template"],
                scan_result=data["scan_result"]
            )
            session.add(scan)
        
        try:
            await session.commit()
            print("Successfully added dummy code scans")
        except Exception as e:
            await session.rollback()
            print(f"Error adding dummy data: {str(e)}")



async def main(action: str):
    if action == "create":
        await create_tables()
        #await populate_dummy_code_mappings()
    elif action == "reset":
        await empty_tables()
    elif action == "populate":
        await populate_dummy_code_mappings()
    elif action == "populate_scans":
        await populate_dummy_code_scans()
    else:
        raise ValueError("Use 'create', 'reset', or 'populate'")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python manage_db.py [create|reset|populate]")
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1]))
    
