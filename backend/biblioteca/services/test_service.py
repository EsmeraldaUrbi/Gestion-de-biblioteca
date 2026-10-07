from biblioteca.repositories.test_repository import TestRepository

class TestService:
    @staticmethod
    def get_system_status():
        # Aquí irían las reglas de negocio, validaciones, límites, etc.
        db_message = TestRepository.get_status_message()
        return f"Lógica de negocio ejecutada. {db_message}"