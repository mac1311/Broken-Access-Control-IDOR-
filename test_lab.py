"""
Script de verificación y demostración rápida de IDOR (Broken Access Control)
Permite probar la lógica sin necesidad de levantar el servidor web manualmente.
"""
from main import SessionLocal, seed_data, ver_pedido_vulnerable, ver_pedido_seguro, Usuario
from fastapi import HTTPException

def ejecutar_demostracion():
    db = SessionLocal()
    seed_data()

    alice = db.query(Usuario).filter(Usuario.id == 1).first()
    bob = db.query(Usuario).filter(Usuario.id == 2).first()

    print("=" * 65)
    print("DEMOSTRACIÓN: BROKEN ACCESS CONTROL (IDOR)")
    print("=" * 65)
    print(f"Usuarios en el sistema:")
    print(f" - Usuario ID 1: {alice.nombre} (Dueña del Pedido 1)")
    print(f" - Usuario ID 2: {bob.nombre} (Atacante - Dueño del Pedido 2)")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. CASO VULNERABLE
    # -------------------------------------------------------------
    print("\n[1] PROBANDO ENDPOINT VULNERABLE: GET /vulnerable/pedidos/1")
    print("Escenario: Bob intenta acceder al Pedido 1 (que es de Alice).")
    try:
        pedido = ver_pedido_vulnerable(pedido_id=1, db=db)
        print("  -> ¡VULNERABILIDAD EXITOSA!")
        print(f"     Se expuso el pedido #{pedido['id']}: '{pedido['descripcion']}' (${pedido['total']})")
        print(f"     Dueño real del pedido: Usuario #{pedido['dueno_id']}")
    except HTTPException as e:
        print(f"  -> Error: {e.status_code} - {e.detail}")

    # -------------------------------------------------------------
    # 2. CASO SEGURO (INTENTO DE ATAQUE)
    # -------------------------------------------------------------
    print("\n[2] PROBANDO ENDPOINT SEGURO: GET /seguro/pedidos/1")
    print("Escenario: Bob (autenticado con ID 2) intenta ver el Pedido 1 (de Alice).")
    try:
        pedido = ver_pedido_seguro(pedido_id=1, usuario=bob, db=db)
        print(f"  -> ERROR: Se permitió el acceso al pedido #{pedido['id']}")
    except HTTPException as e:
        print("  -> ¡ATAQUE DETENIDO!")
        print(f"     Código de respuesta: {e.status_code} ({e.detail})")
        print("     Explicación: El backend validó 'Pedido.dueno_id == usuario.id'. Como no coincide, no devuelve datos.")

    # -------------------------------------------------------------
    # 3. CASO SEGURO (ACCESO LEGÍTIMO)
    # -------------------------------------------------------------
    print("\n[3] PROBANDO ENDPOINT SEGURO (LEGÍTIMO): GET /seguro/pedidos/1")
    print("Escenario: Alice (autenticada con ID 1) consulta su propio Pedido 1.")
    try:
        pedido = ver_pedido_seguro(pedido_id=1, usuario=alice, db=db)
        print("  -> ¡ACCESO PERMITIDO!")
        print(f"     Pedido #{pedido['id']}: '{pedido['descripcion']}' (${pedido['total']})")
        print("     Explicación: Alice es la legítima dueña del recurso.")
    except HTTPException as e:
        print(f"  -> Error: {e.status_code} - {e.detail}")

    print("\n" + "=" * 65)

    db.close()

if __name__ == "__main__":
    ejecutar_demostracion()
