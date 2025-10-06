import json
import pytest


class TestContacts:
    """Testes para os endpoints de contatos."""

    def test_get_contacts_empty(self, client):
        """Testa buscar contatos quando não há nenhum."""
        response = client.get("/contacts/")
        assert response.status_code == 200
        assert response.json == []

    def test_create_contact_success(self, client):
        """Testa criação de contato com sucesso."""
        contact_data = {"email": "contato@exemplo.com"}

        response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["email"] == contact_data["email"].lower()
        assert "contacts_pk" in data

    def test_create_contact_email_normalization(self, client):
        """Testa normalização de email (lowercase e trim)."""
        contact_data = {"email": "  CONTATO@EXEMPLO.COM  "}

        response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["email"] == "contato@exemplo.com"

    def test_create_contact_missing_email(self, client):
        """Testa criação de contato sem email."""
        contact_data = {}

        response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )

        assert response.status_code == 400

    def test_create_contact_empty_email(self, client):
        """Testa criação de contato com email vazio."""
        contact_data = {"email": ""}

        response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )

        assert response.status_code == 400
        assert "Email is required" in response.get_json()["message"]

    def test_create_contact_whitespace_email(self, client):
        """Testa criação de contato com email só com espaços."""
        contact_data = {"email": "   "}

        response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )

        assert response.status_code == 400
        assert "Email is required" in response.get_json()["message"]

    def test_create_contact_duplicate_email(self, client):
        """Testa criação de contato com email duplicado."""
        contact_data = {"email": "contato@exemplo.com"}

        # Cria o primeiro contato
        response1 = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        assert response1.status_code == 201

        # Tenta criar outro contato com mesmo email
        response2 = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        assert response2.status_code == 400
        assert "Email already exists" in response2.get_json()["message"]

    def test_create_contact_duplicate_email_case_insensitive(self, client):
        """Testa duplicação de email ignorando case."""
        # Cria primeiro contato
        contact_data1 = {"email": "contato@exemplo.com"}

        response1 = client.post(
            "/contacts/",
            data=json.dumps(contact_data1),
            content_type="application/json",
        )
        assert response1.status_code == 201

        # Tenta criar com email em maiúscula
        contact_data2 = {"email": "CONTATO@EXEMPLO.COM"}

        response2 = client.post(
            "/contacts/",
            data=json.dumps(contact_data2),
            content_type="application/json",
        )
        assert response2.status_code == 400
        assert "Email already exists" in response2.get_json()["message"]

    def test_get_contacts_with_data(self, client):
        """Testa buscar contatos quando há dados."""
        # Cria alguns contatos
        contacts = [
            {"email": "contato1@exemplo.com"},
            {"email": "contato2@exemplo.com"},
            {"email": "contato3@exemplo.com"},
        ]

        for contact_data in contacts:
            client.post(
                "/contacts/",
                data=json.dumps(contact_data),
                content_type="application/json",
            )

        response = client.get("/contacts/")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3

    def test_get_contacts_ordered_desc(self, client):
        """Testa se contatos são retornados em ordem decrescente por ID."""
        # Cria contatos
        contacts = [
            {"email": "contato1@exemplo.com"},
            {"email": "contato2@exemplo.com"},
            {"email": "contato3@exemplo.com"},
        ]

        created_ids = []
        for contact_data in contacts:
            response = client.post(
                "/contacts/",
                data=json.dumps(contact_data),
                content_type="application/json",
            )
            created_ids.append(response.get_json()["contacts_pk"])

        # Busca todos os contatos
        response = client.get("/contacts/")
        assert response.status_code == 200
        data = response.get_json()

        # Verifica ordem decrescente
        returned_ids = [contact["contacts_pk"] for contact in data]
        assert returned_ids == sorted(created_ids, reverse=True)

    def test_get_contact_by_id_success(self, client):
        """Testa buscar contato específico por ID."""
        # Cria um contato
        contact_data = {"email": "contato@exemplo.com"}

        create_response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        contact_id = create_response.get_json()["contacts_pk"]

        # Busca o contato
        response = client.get(f"/contacts/{contact_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["contacts_pk"] == contact_id
        assert data["email"] == contact_data["email"]

    def test_get_contact_by_id_not_found(self, client):
        """Testa buscar contato que não existe."""
        response = client.get("/contacts/999")
        assert response.status_code == 404
        assert "Contact not found" in response.get_json()["message"]

    def test_update_contact_success(self, client):
        """Testa atualização de contato com sucesso."""
        # Cria um contato
        contact_data = {"email": "contato@exemplo.com"}

        create_response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        contact_id = create_response.get_json()["contacts_pk"]

        # Atualiza o contato
        update_data = {"email": "novo.contato@exemplo.com"}

        response = client.put(
            f"/contacts/{contact_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == update_data["email"]

    def test_update_contact_email_normalization(self, client):
        """Testa normalização de email na atualização."""
        # Cria um contato
        contact_data = {"email": "contato@exemplo.com"}

        create_response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        contact_id = create_response.get_json()["contacts_pk"]

        # Atualiza com email não normalizado
        update_data = {"email": "  NOVO.CONTATO@EXEMPLO.COM  "}

        response = client.put(
            f"/contacts/{contact_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "novo.contato@exemplo.com"

    def test_update_contact_not_found(self, client):
        """Testa atualização de contato que não existe."""
        update_data = {"email": "novo.contato@exemplo.com"}

        response = client.put(
            "/contacts/999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 404
        assert "Contact not found" in response.get_json()["message"]

    def test_update_contact_duplicate_email(self, client):
        """Testa atualização com email que já existe."""
        # Cria dois contatos
        contacts = [
            {"email": "contato1@exemplo.com"},
            {"email": "contato2@exemplo.com"},
        ]

        contact_ids = []
        for contact_data in contacts:
            response = client.post(
                "/contacts/",
                data=json.dumps(contact_data),
                content_type="application/json",
            )
            contact_ids.append(response.get_json()["contacts_pk"])

        # Tenta atualizar o segundo contato com email do primeiro
        update_data = {"email": "contato1@exemplo.com"}

        response = client.put(
            f"/contacts/{contact_ids[1]}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Email already exists" in response.get_json()["message"]

    def test_update_contact_same_email(self, client):
        """Testa atualização mantendo o mesmo email."""
        # Cria um contato
        contact_data = {"email": "contato@exemplo.com"}

        create_response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        contact_id = create_response.get_json()["contacts_pk"]

        # Atualiza com o mesmo email
        update_data = {"email": "contato@exemplo.com"}

        response = client.put(
            f"/contacts/{contact_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == contact_data["email"]

    def test_delete_contact_success(self, client):
        """Testa exclusão de contato com sucesso."""
        # Cria um contato
        contact_data = {"email": "contato@exemplo.com"}

        create_response = client.post(
            "/contacts/", data=json.dumps(contact_data), content_type="application/json"
        )
        contact_id = create_response.get_json()["contacts_pk"]

        # Exclui o contato
        response = client.delete(f"/contacts/{contact_id}")
        assert response.status_code == 200
        assert "Contact deleted successfully" in response.get_json()["message"]

        # Verifica se o contato foi realmente excluído
        get_response = client.get(f"/contacts/{contact_id}")
        assert get_response.status_code == 404

    def test_delete_contact_not_found(self, client):
        """Testa exclusão de contato que não existe."""
        response = client.delete("/contacts/999")
        assert response.status_code == 404
        assert "Contact not found" in response.get_json()["message"]
