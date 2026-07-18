from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Test root and v1 health endpoints return operational statuses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    response_v1 = client.get("/api/v1/system/health")
    assert response_v1.status_code == 200
    assert response_v1.json()["status"] == "healthy"

def test_system_version(client: TestClient):
    """Test version query endpoints return correct metadata descriptors."""
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert "project_name" in response.json()

def test_registration_and_authentication(client: TestClient):
    """Test full auth registration, logins, token acquisition, and route guard checks."""
    user_payload = {
        "email": "tester@testcompany.com",
        "password": "secure_password_test",
        "role": "Developer"
    }

    # 1. Register User
    reg_response = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == user_payload["email"]
    assert reg_response.json()["role"] == "Developer"
    assert "id" in reg_response.json()

    # 2. Login User
    login_payload = {
        "email": user_payload["email"],
        "password": user_payload["password"]
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Access Protected /me Route
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == user_payload["email"]

def test_auth_expansion_flow(client: TestClient):
    """Test token refresh, profile password updates, logout sessions, recovery requests, and resets."""
    # 1. Register User
    user_payload = {
        "email": "expander@test.com",
        "password": "old_password_val",
        "role": "Developer"
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Refresh Token Session
    ref_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert ref_res.status_code == 200
    rotated_tokens = ref_res.json()
    assert "access_token" in rotated_tokens
    assert rotated_tokens["access_token"] != tokens["access_token"]

    # 4. Secure Profile Update (Change password)
    headers = {"Authorization": f"Bearer {rotated_tokens['access_token']}"}
    prof_res = client.put("/api/v1/auth/profile", headers=headers, json={
        "current_password": user_payload["password"],
        "new_password": "new_password_val"
    })
    assert prof_res.status_code == 200

    # 5. Verify Login with New Password
    login_new_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": "new_password_val"
    })
    assert login_new_res.status_code == 200
    new_tokens = login_new_res.json()

    # 6. Logout Session
    headers_logout = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    logout_res = client.post("/api/v1/auth/logout", headers=headers_logout)
    assert logout_res.status_code == 200

    # 7. Request Password Recovery (Forgot Password)
    forgot_res = client.post("/api/v1/auth/forgot-password", json={
        "email": user_payload["email"]
    })
    assert forgot_res.status_code == 200
    assert "debug_token" in forgot_res.json()
    recovery_token = forgot_res.json()["debug_token"]

    # 8. Reset Password
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "email": user_payload["email"],
        "token": recovery_token,
        "new_password": "final_password_val"
    })
    assert reset_res.status_code == 200

    # 9. Verify Final Login
    login_final_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": "final_password_val"
    })
    assert login_final_res.status_code == 200

def test_syntax_validation_flow(client: TestClient):
    """Test AST Python checking, Java bracket parsing, and file extension validation checks."""
    # 1. Register and Login
    user_payload = {
        "email": "syntaxer@test.com",
        "password": "syntax_password_val",
        "role": "Developer"
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    
    login_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    tokens = login_res.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 2. Get the seeded default Project ID
    proj_res = client.get("/api/v1/submissions/projects", headers=headers)
    assert proj_res.status_code == 200
    assert len(proj_res.json()) > 0
    project_id = proj_res.json()[0]["id"]

    # 3. Paste VALID Python code
    valid_py = "def main():\n    print('Hello World')\n"
    py_ok_res = client.post("/api/v1/submissions/paste-code", headers=headers, json={
        "project_id": project_id,
        "submission_type": "paste",
        "raw_code": valid_py,
        "language": "python"
    })
    assert py_ok_res.status_code == 201

    # 4. Paste INVALID Python code (expect 400 Bad Request)
    invalid_py = "def main(\n"
    py_fail_res = client.post("/api/v1/submissions/paste-code", headers=headers, json={
        "project_id": project_id,
        "submission_type": "paste",
        "raw_code": invalid_py,
        "language": "python"
    })
    assert py_fail_res.status_code == 400
    assert "Python Syntax Error" in py_fail_res.json()["detail"]

    # 5. Paste VALID Java code
    valid_java = "public class Main {\n    public static void main(String[] args) {\n        int x = 5;\n    }\n}\n"
    java_ok_res = client.post("/api/v1/submissions/paste-code", headers=headers, json={
        "project_id": project_id,
        "submission_type": "paste",
        "raw_code": valid_java,
        "language": "java"
    })
    assert java_ok_res.status_code == 201

    # 6. Paste INVALID Java code (missing closing brace - expect 400 Bad Request)
    invalid_java = "public class Main {\n    public static void main(String[] args) {\n"
    java_fail_res = client.post("/api/v1/submissions/paste-code", headers=headers, json={
        "project_id": project_id,
        "submission_type": "paste",
        "raw_code": invalid_java,
        "language": "java"
    })
    assert java_fail_res.status_code == 400
    assert "Java Syntax Error" in java_fail_res.json()["detail"]

    # 7. Upload file with INVALID extension (expect 400 Bad Request)
    files = {"file": ("script.txt", b"import os\n", "text/plain")}
    data = {"project_id": project_id}
    upload_fail_res = client.post("/api/v1/submissions/upload", headers=headers, files=files, data=data)
    assert upload_fail_res.status_code == 400
    assert "Unsupported file format" in upload_fail_res.json()["detail"]

def test_project_management_flow(client: TestClient):
    """Test project CRUD operations, keyword searching, paginated lists, sorting, and submissions filtering."""
    # 1. Register and Login
    user_payload = {
        "email": "manager@test.com",
        "password": "manager_password_val",
        "role": "Developer"
    }
    client.post("/api/v1/auth/register", json=user_payload)
    login_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    tokens = login_res.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 2. Create Project A and Project B (In addition to the seeded default project)
    proj_a_res = client.post("/api/v1/projects", headers=headers, json={
        "name": "Project Alpha Container",
        "description": "Alpha security audits"
    })
    assert proj_a_res.status_code == 201
    proj_a_id = proj_a_res.json()["id"]

    proj_b_res = client.post("/api/v1/projects", headers=headers, json={
        "name": "Project Beta Container",
        "description": "Beta review repository"
    })
    assert proj_b_res.status_code == 201
    proj_b_id = proj_b_res.json()["id"]

    # 3. Search: matching "Beta" should return 1 project
    search_res = client.get("/api/v1/projects?search=Beta", headers=headers)
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert search_res.json()["items"][0]["name"] == "Project Beta Container"

    # 4. Update Project A properties
    update_res = client.put(f"/api/v1/projects/{proj_a_id}", headers=headers, json={
        "name": "Project Alpha Renamed",
        "description": "Updated description"
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Project Alpha Renamed"

    # 5. Sorting check: Name ascending
    sort_res = client.get("/api/v1/projects?sort_by=name&sort_order=asc", headers=headers)
    assert sort_res.json()["total"] == 3  # Seeded default + Alpha Renamed + Beta Container
    names = [p["name"] for p in sort_res.json()["items"]]
    # Default project is usually seeded as "Default Project"
    assert sorted(names) == names

    # 6. Create 3 Submissions inside Project B
    for i in range(3):
        client.post("/api/v1/submissions/paste-code", headers=headers, json={
            "project_id": proj_b_id,
            "submission_type": "paste",
            "raw_code": "def main():\n    pass\n",
            "language": "python"
        })

    # 7. Paginated submissions retrieve check (page 1, size 2)
    subs_res = client.get(f"/api/v1/projects/{proj_b_id}/submissions?page=1&size=2", headers=headers)
    assert subs_res.status_code == 200
    assert subs_res.json()["total"] == 3
    assert len(subs_res.json()["items"]) == 2
    assert subs_res.json()["pages"] == 2

    # 8. Check project findings route
    findings_res = client.get(f"/api/v1/reports/project/{proj_b_id}/findings", headers=headers)
    assert findings_res.status_code == 200
    assert isinstance(findings_res.json(), list)

    # 9. Check report exports (JSON, MD, HTML, PDF)
    reports_res = client.get(f"/api/v1/reports/project/{proj_b_id}", headers=headers)
    assert reports_res.status_code == 200
    if len(reports_res.json()) > 0:
        rep_id = reports_res.json()[0]["id"]
        for fmt in ["JSON", "MD", "HTML", "PDF"]:
            exp_res = client.post(f"/api/v1/reports/{rep_id}/export", headers=headers, json={
                "report_id": rep_id,
                "export_type": fmt
            })
            assert exp_res.status_code == 201
            assert exp_res.json()["export_type"] == fmt
            assert "file_path" in exp_res.json()

    # 10. Delete Project A Renamed
    del_res = client.delete(f"/api/v1/projects/{proj_a_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify Project A Renamed is gone
    get_del_res = client.get(f"/api/v1/projects/{proj_a_id}", headers=headers)
    assert get_del_res.status_code == 404


