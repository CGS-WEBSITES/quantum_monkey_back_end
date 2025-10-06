import json
import pytest


class TestUsers:
    """Testes para os endpoints de usuários."""

    def test_get_users_empty(self, client):
        """Testa buscar usuários quando não há nenhum."""
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json == []

    def test_create_user_success(self, client):
        """Testa criação de usuário com sucesso."""
        user_data = {"name": "João Silva", "email": "joao@exemplo.com"}

        response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert "users_pk" in data

    def test_create_user_missing_name(self, client):
        """Testa criação de usuário sem nome."""
        user_data = {"email": "joao@exemplo.com"}

        response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )

        assert response.status_code == 400

    def test_create_user_missing_email(self, client):
        """Testa criação de usuário sem email."""
        user_data = {"name": "João Silva"}

        response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )

        assert response.status_code == 400

    def test_create_user_duplicate_email(self, client):
        """Testa criação de usuário com email duplicado."""
        user_data = {"name": "João Silva", "email": "joao@exemplo.com"}

        # Cria o primeiro usuário
        response1 = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )
        assert response1.status_code == 201

        # Tenta criar outro usuário com mesmo email
        user_data2 = {"name": "Maria Silva", "email": "joao@exemplo.com"}

        response2 = client.post(
            "/users/", data=json.dumps(user_data2), content_type="application/json"
        )
        assert response2.status_code == 400
        assert "Email already exists" in response2.get_json()["message"]

    def test_get_users_with_data(self, client):
        """Testa buscar usuários quando há dados."""
        # Cria alguns usuários
        users = [
            {"name": "João Silva", "email": "joao@exemplo.com"},
            {"name": "Maria Santos", "email": "maria@exemplo.com"},
        ]

        for user_data in users:
            client.post(
                "/users/", data=json.dumps(user_data), content_type="application/json"
            )

        response = client.get("/users/")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_user_by_id_success(self, client):
        """Testa buscar usuário específico por ID."""
        # Cria um usuário
        user_data = {"name": "João Silva", "email": "joao@exemplo.com"}

        create_response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )
        user_id = create_response.get_json()["users_pk"]

        # Busca o usuário
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["users_pk"] == user_id
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]

    def test_get_user_by_id_not_found(self, client):
        """Testa buscar usuário que não existe."""
        response = client.get("/users/999")
        assert response.status_code == 404
        assert "User not found" in response.get_json()["message"]

    def test_update_user_success(self, client):
        """Testa atualização de usuário com sucesso."""
        # Cria um usuário
        user_data = {"name": "João Silva", "email": "joao@exemplo.com"}

        create_response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )
        user_id = create_response.get_json()["users_pk"]

        # Atualiza o usuário
        update_data = {"name": "João Santos", "email": "joao.santos@exemplo.com"}

        response = client.put(
            f"/users/{user_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]

    def test_update_user_not_found(self, client):
        """Testa atualização de usuário que não existe."""
        update_data = {"name": "João Santos", "email": "joao.santos@exemplo.com"}

        response = client.put(
            "/users/999", data=json.dumps(update_data), content_type="application/json"
        )

        assert response.status_code == 404
        assert "User not found" in response.get_json()["message"]

    def test_update_user_duplicate_email(self, client):
        """Testa atualização com email que já existe."""
        # Cria dois usuários
        users = [
            {"name": "João Silva", "email": "joao@exemplo.com"},
            {"name": "Maria Santos", "email": "maria@exemplo.com"},
        ]

        user_ids = []
        for user_data in users:
            response = client.post(
                "/users/", data=json.dumps(user_data), content_type="application/json"
            )
            user_ids.append(response.get_json()["users_pk"])

        # Tenta atualizar o segundo usuário com email do primeiro
        update_data = {"name": "Maria Silva", "email": "joao@exemplo.com"}

        response = client.put(
            f"/users/{user_ids[1]}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Email already exists" in response.get_json()["message"]

    def test_delete_user_success(self, client):
        """Testa exclusão de usuário com sucesso."""
        # Cria um usuário
        user_data = {"name": "João Silva", "email": "joao@exemplo.com"}

        create_response = client.post(
            "/users/", data=json.dumps(user_data), content_type="application/json"
        )
        user_id = create_response.get_json()["users_pk"]

        # Exclui o usuário
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        assert "User deleted successfully" in response.get_json()["message"]

        # Verifica se o usuário foi realmente excluído
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client):
        """Testa exclusão de usuário que não existe."""
        response = client.delete("/users/999")
        assert response.status_code == 404
        assert "User not found" in response.get_json()["message"]
